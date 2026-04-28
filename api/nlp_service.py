import spacy
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

_nlp = None
_embedder = None


def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
            _nlp = spacy.load("en_core_web_sm")
    return _nlp


def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def extract_concepts(text: str) -> list[str]:
    nlp = get_nlp()
    doc = nlp(text)
    concepts = set()
    for chunk in doc.noun_chunks:
        cleaned = chunk.text.strip().lower()
        if len(cleaned) > 2 and not all(t.is_stop for t in chunk):
            concepts.add(cleaned)
    for ent in doc.ents:
        concepts.add(ent.text.strip().lower())
    return list(concepts)


def score_similarity(text_a: str, text_b: str) -> float:
    embedder = get_embedder()
    emb_a = embedder.encode([text_a])
    emb_b = embedder.encode([text_b])
    score = cosine_similarity(emb_a, emb_b)[0][0]
    return float(np.clip(score, 0.0, 1.0))


def score_concepts_against_explanation(concepts: list[str], explanation: str) -> dict[str, float]:
    if not concepts:
        return {}
    embedder = get_embedder()
    concept_embs = embedder.encode(concepts)
    explanation_emb = embedder.encode([explanation])
    scores = cosine_similarity(explanation_emb, concept_embs)[0]
    return {concept: float(np.clip(score, 0.0, 1.0)) for concept, score in zip(concepts, scores)}


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def retrieve_relevant_chunks(query: str, chunks: list[str], top_k: int = 3) -> list[str]:
    if not chunks:
        return []
    embedder = get_embedder()
    query_emb = embedder.encode([query])
    chunk_embs = embedder.encode(chunks)
    scores = cosine_similarity(query_emb, chunk_embs)[0]
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [chunks[i] for i in top_indices]
