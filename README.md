# LearnLoop 

> AI-powered learning companion using the Feynman Technique, NLP gap detection, and Socratic tutoring.

## Features
- **Feynman engine** — explain a topic in your own words, get scored
- **Semantic gap analysis** — sentence-transformers cosine similarity per concept
- **Interactive knowledge map** — NetworkX + pyvis graph (green = known, red = gap)
- **Socratic tutor** — Claude targets only your gaps, never gives direct answers
- **RAG** — paste notes or upload a PDF to ground the tutor in your own material
- **User pattern learning** — tracks weak topics, learning style, misconceptions across sessions

## Tech Stack
| Layer | Tech |
|---|---|
| Frontend | Streamlit + pyvis |
| Backend | FastAPI + uvicorn |
| LLM | Claude claude-sonnet-4-20250514 via Anthropic SDK |
| NLP | spaCy (en_core_web_sm) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Graphs | NetworkX + pyvis |
| RAG | LangChain text splitter + FAISS |
| Storage | SQLite (sessions, patterns, chat history) |

## Setup

```bash
#Run these one at a time in PowerShell:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# set up your .env
copy .env.example .env

# Window 1: Backend
venv\Scripts\activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Window 2: Frontend
venv\Scripts\activate
streamlit run app.py
```

Open http://localhost:8501

## Project Structure
```
learnloop/
├── app.py                  # Streamlit UI
├── api/
│   ├── main.py             # FastAPI routes
│   ├── claude_service.py   # 3 prompt chains (gap, graph, tutor)
│   ├── nlp_service.py      # spaCy + sentence-transformers
│   ├── graph_service.py    # NetworkX + pyvis rendering
│   ├── db_service.py       # SQLite persistence
│   └── models.py           # Pydantic schemas
├── data/
│   ├── sessions/           # JSON session backups
│   └── learnloop.db        # SQLite database
├── requirements.txt
├── run.sh
└── .env
```

## ML / AI Concepts Used
- **NLP** — spaCy noun chunk + NER extraction
- **Semantic similarity** — sentence-transformers cosine similarity for mastery scoring
- **Knowledge graphs** — NetworkX directed graph of concept relationships
- **Intelligent Tutoring Systems (ITS)** — student model + gap-targeted instruction
- **Prompt chaining** — 3 structured Claude calls with Pydantic-validated JSON output
- **RAG** — user notes chunked and retrieved to ground tutor responses
- **User pattern learning** — persistent profile updated across sessions
