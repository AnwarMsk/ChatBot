"""
setup_pgvector.py — Script de configuration pgvector (à exécuter une seule fois).

Ce script effectue les opérations suivantes :
  1. Active l'extension pgvector dans PostgreSQL
  2. Ajoute la colonne 'embedding vector(384)' à la table faqs
  3. Charge le modèle sentence-transformers multilingue
  4. Génère les embeddings pour chaque FAQ et les stocke dans la base

Usage :
    python setup_pgvector.py

Prérequis :
    pip install sentence-transformers pgvector
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
from db import get_connection

# ── Modèle d'embeddings ─────────────────────────────────────────────
# paraphrase-multilingual-MiniLM-L12-v2 :
#   - Supporte 50+ langues dont le français
#   - Génère des vecteurs de 384 dimensions
#   - Léger (~420 Mo) et rapide (~14k tokens/s sur CPU)
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
VECTOR_DIM = 384


def activer_extension(cursor):
    """Active l'extension pgvector si elle n'est pas déjà installée."""
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
    print("[OK] Extension pgvector activée.")


def ajouter_colonne_embedding(cursor):
    """Ajoute la colonne embedding à la table faqs (ignorée si déjà existante)."""
    cursor.execute("""
        ALTER TABLE faqs
        ADD COLUMN IF NOT EXISTS embedding vector(%s)
    """, (VECTOR_DIM,))
    print(f"[OK] Colonne embedding vector({VECTOR_DIM}) ajoutée à la table faqs.")


def creer_index_hnsw(cursor):
    """
    Crée un index HNSW (Hierarchical Navigable Small World) sur la colonne embedding.

    HNSW est l'algorithme d'indexation le plus performant pour la recherche
    de voisins les plus proches approximatifs (ANN). Il offre un excellent
    compromis entre vitesse de recherche et précision.

    L'opérateur vector_cosine_ops indique que l'index est optimisé pour
    la distance cosinus (<=> operator).
    """
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS faqs_embedding_hnsw_idx
        ON faqs
        USING hnsw (embedding vector_cosine_ops)
    """)
    print("[OK] Index HNSW créé sur faqs.embedding (cosine similarity).")


def generer_et_stocker_embeddings(cursor, model):
    """
    Pour chaque FAQ dans la table, génère son embedding et le stocke.

    Le modèle encode la QUESTION (pas la réponse) car c'est la question
    de l'utilisateur que l'on compare avec les questions de la FAQ.
    """
    cursor.execute("SELECT id, question FROM faqs ORDER BY id")
    faqs = cursor.fetchall()

    print(f"\n[INFO] Génération des embeddings pour {len(faqs)} FAQs...")

    for faq_id, question in faqs:
        # Encode la question → numpy array de 384 floats
        embedding = model.encode(question, normalize_embeddings=True)

        cursor.execute(
            "UPDATE faqs SET embedding = %s WHERE id = %s",
            (embedding, faq_id)
        )
        print(f"  [{faq_id}] Encodé : {question[:60]}...")

    print(f"\n[OK] {len(faqs)} embeddings générés et stockés.")


def main():
    print("=" * 60)
    print("  Setup pgvector — Chatbot Universitaire EMI")
    print("=" * 60)

    # ── Étape 1 : Charger le modèle ────────────────────────────────
    print(f"\n[INFO] Chargement du modèle '{MODEL_NAME}'...")
    print("       (Premier lancement : téléchargement ~420 Mo)")
    model = SentenceTransformer(MODEL_NAME)
    print(f"[OK] Modèle chargé — dimension des vecteurs : {VECTOR_DIM}")

    # ── Étape 2 : Connexion RAW (sans register_vector) ─────────────
    # On ne peut pas appeler register_vector() avant que l'extension
    # pgvector soit installée. On utilise donc une connexion psycopg2
    # brute pour les opérations de schéma.
    print("\n[INFO] Connexion à PostgreSQL (phase setup)...")
    import os
    from dotenv import load_dotenv
    load_dotenv()

    raw_conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "84.8.219.24"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "university_chatbot"),
        user=os.getenv("DB_USER", "chatbot_user"),
        password=os.getenv("DB_PASSWORD", "mysecretpassword"),
        options="-c client_encoding=UTF8"
    )
    raw_cursor = raw_conn.cursor()

    try:
        activer_extension(raw_cursor)
        ajouter_colonne_embedding(raw_cursor)
        creer_index_hnsw(raw_cursor)
        raw_conn.commit()
        print("[OK] Schéma configuré.")
    except Exception as e:
        raw_conn.rollback()
        print(f"\n[ERREUR] Phase setup : {e}")
        raise
    finally:
        raw_cursor.close()
        raw_conn.close()

    # ── Étape 3 : Connexion avec register_vector ───────────────────
    # Maintenant que l'extension existe, get_connection() peut appeler
    # register_vector() sans erreur.
    print("\n[INFO] Connexion à PostgreSQL (phase embeddings)...")
    conn = get_connection()
    cursor = conn.cursor()

    try:
        generer_et_stocker_embeddings(cursor, model)
        conn.commit()
        print("\n[DONE] Configuration pgvector terminée avec succès.")
        print("       Vous pouvez maintenant lancer : python app.py")
    except Exception as e:
        conn.rollback()
        print(f"\n[ERREUR] Phase embeddings : {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
