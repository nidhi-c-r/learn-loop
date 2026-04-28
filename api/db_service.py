import sqlite3
import json
import os
from datetime import datetime
from api.models import UserPattern

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "learnloop.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TEXT,
            topic TEXT,
            explanation TEXT,
            gap_report TEXT,
            graph TEXT,
            overall_score REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_patterns (
            session_id TEXT PRIMARY KEY,
            weak_topics TEXT,
            strong_topics TEXT,
            avg_score REAL,
            preferred_style TEXT,
            total_sessions INTEGER,
            last_seen TEXT,
            common_misconceptions TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            topic TEXT,
            role TEXT,
            content TEXT,
            timestamp TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS rag_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            chunk TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_session(session_id: str, topic: str, explanation: str, gap_report: dict, graph: dict, score: float):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session_id, datetime.now().isoformat(), topic, explanation,
          json.dumps(gap_report), json.dumps(graph), score))
    conn.commit()
    conn.close()


def get_session_history(session_id: str) -> list[dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM sessions WHERE session_id = ? ORDER BY created_at DESC", (session_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_pattern(session_id: str) -> UserPattern:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM user_patterns WHERE session_id = ?", (session_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return UserPattern(
            session_id=session_id,
            weak_topics=json.loads(row["weak_topics"] or "[]"),
            strong_topics=json.loads(row["strong_topics"] or "[]"),
            avg_score=row["avg_score"] or 0.0,
            preferred_explanation_style=row["preferred_style"] or "detailed",
            total_sessions=row["total_sessions"] or 0,
            last_seen=row["last_seen"] or "",
            common_misconceptions=json.loads(row["common_misconceptions"] or "[]"),
        )
    return UserPattern(session_id=session_id)


def update_user_pattern(pattern: UserPattern):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO user_patterns VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        pattern.session_id,
        json.dumps(pattern.weak_topics),
        json.dumps(pattern.strong_topics),
        pattern.avg_score,
        pattern.preferred_explanation_style,
        pattern.total_sessions,
        datetime.now().isoformat(),
        json.dumps(pattern.common_misconceptions),
    ))
    conn.commit()
    conn.close()


def save_chat_message(session_id: str, topic: str, role: str, content: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO chat_history (session_id, topic, role, content, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, topic, role, content, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_chat_history(session_id: str, topic: str) -> list[dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT role, content FROM chat_history
        WHERE session_id = ? AND topic = ?
        ORDER BY timestamp ASC
    """, (session_id, topic))
    rows = c.fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def save_rag_chunks(session_id: str, chunks: list[str]):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM rag_chunks WHERE session_id = ?", (session_id,))
    for chunk in chunks:
        c.execute("INSERT INTO rag_chunks (session_id, chunk, created_at) VALUES (?, ?, ?)",
                  (session_id, chunk, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_rag_chunks(session_id: str) -> list[str]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT chunk FROM rag_chunks WHERE session_id = ?", (session_id,))
    rows = c.fetchall()
    conn.close()
    return [r["chunk"] for r in rows]
