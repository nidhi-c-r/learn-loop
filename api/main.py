import os
import json
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if Groq API key is loading properly
print("GROQ KEY:", os.getenv("GROQ_API_KEY"))

from api.models import ExplainRequest, TutorMessage, RAGRequest
from api.db_service import (
    init_db,
    save_session,
    get_user_pattern,
    update_user_pattern,
    save_chat_message,
    get_chat_history,
    save_rag_chunks,
    get_rag_chunks,
    get_session_history,
)

from api.nlp_service import (
    extract_concepts,
    score_concepts_against_explanation,
    chunk_text,
    retrieve_relevant_chunks,
)

# Keep this same if you replaced claude_service.py content with Groq code
from api.claude_service import (
    analyse_gaps,
    build_knowledge_graph,
    socratic_tutor,
    infer_learning_style,
    extract_misconceptions,
)

from api.graph_service import (
    render_pyvis,
    get_graph_stats,
)

app = FastAPI(
    title="LearnLoop API",
    version="1.0.0"
)

# Enable frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    init_db()


@app.post("/analyse")
async def analyse(req: ExplainRequest):
    try:
        # Get previous learning profile
        user_pattern = get_user_pattern(req.session_id)

        # Extract concepts + similarity scores
        concepts = extract_concepts(req.explanation)
        concept_scores = score_concepts_against_explanation(
            concepts,
            req.explanation
        )

        # RAG retrieval if notes exist
        rag_chunks = get_rag_chunks(req.session_id)
        rag_context = ""

        if rag_chunks:
            relevant = retrieve_relevant_chunks(
                req.topic + " " + req.explanation,
                rag_chunks
            )
            rag_context = "\n\n".join(relevant)

        # LLM analysis
        gap_report = analyse_gaps(
            req.topic,
            req.explanation,
            concept_scores,
            user_pattern,
            rag_context
        )

        # Knowledge graph creation
        graph = build_knowledge_graph(
            req.topic,
            req.explanation,
            gap_report
        )

        graph_html = render_pyvis(graph)
        stats = get_graph_stats(graph)

        # Save session
        save_session(
            req.session_id,
            req.topic,
            req.explanation,
            gap_report.model_dump(),
            graph.model_dump(),
            gap_report.overall_score,
        )

        # Get history
        history = get_session_history(req.session_id)
        all_explanations = [
            h.get("explanation", "")
            for h in history
        ]

        all_reports = [gap_report]

        # Update learning profile
        user_pattern.total_sessions += 1

        user_pattern.avg_score = (
            (
                user_pattern.avg_score *
                (user_pattern.total_sessions - 1)
                + gap_report.overall_score
            )
            / user_pattern.total_sessions
        )

        if gap_report.overall_score < 0.5:
            if req.topic not in user_pattern.weak_topics:
                user_pattern.weak_topics.append(req.topic)
        else:
            if req.topic not in user_pattern.strong_topics:
                user_pattern.strong_topics.append(req.topic)

        user_pattern.preferred_explanation_style = infer_learning_style(
            all_explanations
        )

        user_pattern.common_misconceptions = extract_misconceptions(
            all_reports
        )

        update_user_pattern(user_pattern)

        return {
            "gap_report": gap_report.model_dump(),
            "graph_html": graph_html,
            "graph": graph.model_dump(),
            "stats": stats,
            "user_pattern": user_pattern.model_dump(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/tutor")
async def tutor(req: TutorMessage):
    try:
        history = get_chat_history(
            req.session_id,
            req.topic
        )

        user_pattern = get_user_pattern(req.session_id)

        sessions = get_session_history(req.session_id)
        gap_report_data = None

        for s in sessions:
            if (
                s.get("topic") == req.topic
                and s.get("gap_report")
            ):
                gap_report_data = json.loads(
                    s["gap_report"]
                )
                break

        if not gap_report_data:
            raise HTTPException(
                status_code=400,
                detail="Run /analyse first for this topic."
            )

        from api.models import GapReport, GapNode

        gaps = [
            GapNode(**g)
            for g in gap_report_data.get("gaps", [])
        ]

        gap_report = GapReport(
            topic=gap_report_data["topic"],
            overall_score=gap_report_data["overall_score"],
            gaps=gaps,
            strengths=gap_report_data.get(
                "strengths",
                []
            ),
            summary=gap_report_data.get(
                "summary",
                ""
            ),
        )

        # RAG retrieval
        rag_chunks = get_rag_chunks(req.session_id)
        rag_context = ""

        if rag_chunks:
            relevant = retrieve_relevant_chunks(
                req.message,
                rag_chunks
            )
            rag_context = "\n\n".join(relevant)

        response = socratic_tutor(
            req.topic,
            req.message,
            gap_report,
            history,
            user_pattern,
            rag_context
        )

        # Save tutor conversation
        save_chat_message(
            req.session_id,
            req.topic,
            "user",
            req.message
        )

        save_chat_message(
            req.session_id,
            req.topic,
            "assistant",
            response.reply
        )

        return response.model_dump()

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/rag/upload-text")
async def upload_rag_text(req: RAGRequest):
    try:
        chunks = chunk_text(req.text)
        save_rag_chunks(
            req.session_id,
            chunks
        )

        return {
            "status": "ok",
            "chunks": len(chunks)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/rag/upload-file")
async def upload_rag_file(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        content = await file.read()

        if file.filename.endswith(".pdf"):
            import fitz

            doc = fitz.open(
                stream=content,
                filetype="pdf"
            )

            text = "\n".join(
                page.get_text()
                for page in doc
            )
        else:
            text = content.decode(
                "utf-8",
                errors="ignore"
            )

        chunks = chunk_text(text)

        save_rag_chunks(
            session_id,
            chunks
        )

        return {
            "status": "ok",
            "chunks": len(chunks),
            "filename": file.filename
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/pattern/{session_id}")
async def get_pattern(session_id: str):
    return get_user_pattern(
        session_id
    ).model_dump()


@app.get("/history/{session_id}")
async def get_history(session_id: str):
    return get_session_history(session_id)


@app.get("/health")
async def health():
    return {
        "status": "ok"
    }