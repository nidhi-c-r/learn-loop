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
You are a strict academic evaluator.

Evaluate the student's understanding of: {topic}

Student Explanation:
{explanation}

Concept Coverage Scores:
{scores_text}

IMPORTANT RULES:
- Be strict, not generous
- If explanation is short, vague, incomplete, or missing technical depth → mark as NOT understood
- Only mark understood=true if the student clearly explains the concept properly
- Real conceptual gaps must be identified
- For weak explanations, multiple gaps should appear
- If the student gives only 1–2 lines, there should usually be several gaps
- Do NOT praise weak answers too much

Return ONLY valid JSON in this exact format:

{{
  "topic": "{topic}",
  "overall_score": 0.0,
  "gaps": [
    {{
      "concept": "",
      "understood": false,
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
You are an expert educational tutor using the Feynman Technique and Socratic Teaching.

Your job is to HELP the student understand the topic deeply.

Topic: {topic}

Student Message:
{user_message}

IMPORTANT RULES:
1. First answer the student's question clearly and directly
2. Then explain in simple student-friendly words
3. Then ask ONE follow-up question to test understanding
4. Do NOT reply with vague phrases like:
   - Let's explore that
   - That's interesting
   - Good start
   - Tell me more
5. Always provide actual teaching value
6. Keep answers short, clear, and educational
7. If the student is wrong, gently correct them
8. If the student asks “why”, explain the reason properly

GOOD EXAMPLE:

Student: Why is air present on Earth?

Tutor:
Air exists on Earth because Earth's gravity holds gases around the planet, forming the atmosphere. Plants also help maintain oxygen through photosynthesis. Without gravity, these gases would escape into space.

Now tell me — why do you think the Moon does not have much atmosphere?

Return only the tutor reply text.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
    )

    # IMPORTANT:
    # Do NOT use _parse_json() here
    # because tutor returns plain text, not JSON

    reply = response.choices[0].message.content.strip()

    return TutorResponse(
        reply=reply,
        follow_up_question=None,
        nodes_improved=[],
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
