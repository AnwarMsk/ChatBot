"""
Script to fix corrupted FAQ data in PostgreSQL.
Clears the existing broken data and re-inserts from faq_universitaire.json
with proper UTF-8 encoding.

Usage (from the nlp/ directory):
    python fix_encoding.py
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
import psycopg2

# ── The exact 8 original FAQs with corrected UTF-8 accents ─────────
# Each entry: (id, question, answer, [keywords])
# Keywords are lowercase, accent-free (the controller strips accents before searching)
FAQS = [
    (
        1,
        "Comment obtenir une attestation de scolarité ou un certificat de scolarité ?",
        "Vous pouvez la demander au service de scolarité de l'EMI ou la télécharger via votre espace étudiant.",
        ["attestation", "scolarite"]
    ),
    (
        2,
        "Quand commencent les examens et les épreuves de la session ?",
        "Le calendrier des examens est affiché au département et sur le site web deux semaines avant le début des épreuves.",
        ["examen", "examens"]
    ),
    (
        3,
        "Comment se réinscrire ou s'inscrire à l'université pour une nouvelle année ?",
        "La réinscription administrative se fait en ligne au début de chaque année universitaire.",
        ["reinscription", "inscription"]
    ),
    (
        4,
        "Comment postuler pour la bourse Minhaty ou obtenir une aide financière étudiante ?",
        "La demande de bourse Minhaty se fait exclusivement en ligne sur le portail national de l'étudiant avec votre code Massar.",
        ["bourse", "minhaty"]
    ),
    (
        5,
        "Où puis-je consulter mon emploi du temps ou mon planning de cours ?",
        "Les emplois du temps sont affichés sur les panneaux de votre département et disponibles sur l'intranet de l'école.",
        ["emploi", "temps"]
    ),
    (
        6,
        "Quelles sont les horaires d'ouverture de la bibliothèque universitaire (biblio, bib) ?",
        "La bibliothèque universitaire est ouverte du lundi au vendredi, de 8h30 à 18h00 sans interruption.",
        ["bibliotheque", "horaire", "ouverture"]
    ),
    (
        7,
        "Comment accéder aux services médicaux ou au centre de santé de l'université ?",
        "Le centre médical de l'université est ouvert tous les matins. Il suffit de présenter votre carte d'étudiant pour toute consultation.",
        ["medical", "medecin", "sante"]
    ),
    (
        8,
        "Quand est-ce que les résultats des examens ou les notes seront affichés ?",
        "Les résultats des modules sont généralement affichés par le département deux semaines après la fin de la session d'examens.",
        ["resultat", "resultats", "notes"]
    ),
]

# ── Execution ───────────────────────────────────────────────────────
def main():
    conn = psycopg2.connect(
        host="84.8.219.24",
        port="5432",
        dbname="university_chatbot",
        user="chatbot_user",
        password="mysecretpassword",
        options="-c client_encoding=UTF8"
    )
    cursor = conn.cursor()

    try:
        # 1. Clear all tables (junction first to respect FK constraints)
        print("[INFO] Clearing existing data...")
        cursor.execute("DELETE FROM faq_keywords")
        cursor.execute("DELETE FROM faqs")
        cursor.execute("DELETE FROM keywords")
        print("[OK] Tables cleared.")

        # 2. Insert FAQs and keywords
        print("\n[INFO] Inserting original 8 FAQs...")
        for (faq_id, question, answer, keywords) in FAQS:
            # Insert FAQ with explicit ID
            cursor.execute(
                "INSERT INTO faqs (id, question, answer) VALUES (%s, %s, %s)",
                (faq_id, question, answer)
            )

            for word in keywords:
                # Insert keyword (ignore if already exists)
                cursor.execute(
                    "INSERT INTO keywords (word) VALUES (%s) ON CONFLICT (word) DO NOTHING",
                    (word,)
                )
                # Get keyword ID
                cursor.execute("SELECT id FROM keywords WHERE word = %s", (word,))
                keyword_id = cursor.fetchone()[0]

                # Link FAQ <-> keyword
                cursor.execute(
                    "INSERT INTO faq_keywords (faq_id, keyword_id) VALUES (%s, %s)",
                    (faq_id, keyword_id)
                )

            print(f"  [{faq_id}] OK - {question}")

        conn.commit()
        print(f"\n[DONE] 8 FAQs inserted with correct UTF-8 encoding.")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()



