import json
import os
from groq import Groq
from api.models import (
    GapReport,
    GapNode,
    KnowledgeGraph,
    GraphNode,
    GraphEdge,
    TutorResponse,
    UserPattern,
)

MODEL = "llama-3.3-70b-versatile"


def get_client():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env file")

    return Groq(api_key=api_key)


def _parse_json(text: str) -> dict:
    text = text.strip()

    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) > 1:
            text = parts[1]
            if text.startswith("json"):
                text = text[4:]

    return json.loads(text.strip())


def analyse_gaps(
    topic: str,
    explanation: str,
    concept_scores: dict[str, float],
    user_pattern: UserPattern,
    rag_context: str = "",
) -> GapReport:
    client = get_client()

    scores_text = "\n".join(
        f"- {k}: {v:.2f}" for k, v in concept_scores.items()
    )

    prompt = f"""
You are an expert educational evaluator.

Analyse this student's explanation of: {topic}

Student Explanation:
{explanation}

Concept Coverage Scores:
{scores_text}

Return ONLY valid JSON in this exact format:
{{
  "topic": "{topic}",
  "overall_score": 0.0,
  "gaps": [
    {{
      "concept": "",
      "understood": true,
      "score": 0.0,
      "feedback": ""
    }}
  ],
  "strengths": [""],
  "summary": ""
}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    data = _parse_json(content)

    gaps = [GapNode(**g) for g in data.get("gaps", [])]

    return GapReport(
        topic=data["topic"],
        overall_score=data["overall_score"],
        gaps=gaps,
        strengths=data.get("strengths", []),
        summary=data["summary"],
    )


def build_knowledge_graph(
    topic: str,
    explanation: str,
    gap_report: GapReport,
) -> KnowledgeGraph:
    client = get_client()

    prompt = f"""
Create a knowledge graph for topic: {topic}

Explanation:
{explanation}

Return ONLY valid JSON:
{{
  "nodes": [
    {{
      "id": "",
      "label": "",
      "score": 0.0,
      "understood": true
    }}
  ],
  "edges": [
    {{
      "source": "",
      "target": "",
      "relation": ""
    }}
  ]
}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    data = _parse_json(content)

    nodes = [GraphNode(**n) for n in data.get("nodes", [])]
    edges = [GraphEdge(**e) for e in data.get("edges", [])]

    return KnowledgeGraph(nodes=nodes, edges=edges)


def socratic_tutor(
    topic: str,
    user_message: str,
    gap_report: GapReport,
    chat_history: list[dict],
    user_pattern: UserPattern,
    rag_context: str = "",
) -> TutorResponse:
    client = get_client()

    prompt = f"""
You are a Socratic tutor for topic: {topic}

Student message:
{user_message}

Rules:
- Never directly give answers
- Ask guiding questions
- Be concise and helpful

Return ONLY valid JSON:
{{
  "reply": "",
  "follow_up_question": "",
  "nodes_improved": []
}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
    )

    content = response.choices[0].message.content
    data = _parse_json(content)

    return TutorResponse(
        reply=data.get("reply", ""),
        follow_up_question=data.get("follow_up_question"),
        nodes_improved=data.get("nodes_improved", []),
    )


def infer_learning_style(explanations: list[str]) -> str:
    if not explanations:
        return "detailed"

    avg_len = sum(len(e.split()) for e in explanations) / len(explanations)

    if avg_len < 40:
        return "concise"
    elif avg_len > 120:
        return "detailed"

    return "moderate"


def extract_misconceptions(gap_reports: list[GapReport]) -> list[str]:
    misconceptions = []
    seen = set()

    for report in gap_reports:
        for gap in report.gaps:
            if not gap.understood and gap.concept not in seen:
                misconceptions.append(gap.concept)
                seen.add(gap.concept)

    return misconceptions[:5]
