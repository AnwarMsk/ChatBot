import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_USER     = os.getenv("DB_USER", "chatbot_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mysecretpassword")
DB_HOST     = os.getenv("DB_HOST", "84.8.219.24")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME     = os.getenv("DB_NAME", "university_chatbot")


def get_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        client_encoding='UTF8'
    )
    return conn


def get_all_faqs():
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


def get_reponse_by_id(faq_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT answer FROM faqs WHERE id = %s", (faq_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        cursor.close()
        conn.close()


def get_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        options="-c client_encoding=UTF8"
    )
    return conn