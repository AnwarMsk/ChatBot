import psycopg2
import numpy as np
import os
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector

load_dotenv()

DB_USER     = os.getenv("DB_USER", "chatbot_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mysecretpassword")
DB_HOST     = os.getenv("DB_HOST", "84.8.219.24")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME     = os.getenv("DB_NAME", "university_chatbot")


def get_connection():
    """
    Returns a psycopg2 connection with:
    - UTF-8 client encoding (prevents ?? garbling of French text)
    - pgvector type registered (enables numpy array ↔ vector column mapping)
    """
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        options="-c client_encoding=UTF8"
    )
    register_vector(conn)  # Needed to read/write vector columns as numpy arrays
    return conn


def get_all_faqs():
    """Fetches all FAQ question/answer pairs (used by V2 TF-IDF engine)."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT question, answer FROM faqs")
        rows = cursor.fetchall()
        return [
            {"question": row[0], "reponse": row[1]}
            for row in rows
        ]
    finally:
        cursor.close()
        conn.close()


def search_by_vector(embedding: np.ndarray, seuil: float = 0.4) -> dict | None:
    """
    V3 — pgvector semantic search.

    Converts the embedding into a PostgreSQL vector and finds the most
    semantically similar FAQ using cosine similarity (<=> operator).

    Args:
        embedding: numpy array (384-dim) from sentence-transformers
        seuil:     minimum cosine similarity score to accept a match (0 to 1)

    Returns:
        dict with 'answer', 'score', 'question' if a match is found above the threshold,
        None otherwise.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT answer,
                   question,
                   1 - (embedding <=> %s) AS score
            FROM faqs
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s
            LIMIT 1
            """,
            (embedding, embedding)
        )
        row = cursor.fetchone()

        if row and row[2] >= seuil:
            return {
                "answer":   row[0],
                "question": row[1],
                "score":    round(float(row[2]), 4)
            }
        return None

    finally:
        cursor.close()
        conn.close()