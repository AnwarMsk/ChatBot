from flask import Flask, request, jsonify
from pgvector_engine import PgVectorEngine

app = Flask(__name__)

# V3 : moteur pgvector (recherche sémantique via PostgreSQL)
engine = PgVectorEngine(seuil_similarite=0.4)


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()

    if not data or "question" not in data:
        return jsonify({"erreur": "Le champ 'question' est requis."}), 400

    question = data["question"].strip()

    if not question:
        return jsonify({"erreur": "La question ne peut pas être vide."}), 400

    if len(question) > 500:
        return jsonify({"erreur": "La question est trop longue (max 500 caractères)."}), 400

    resultat = engine.trouver_reponse(question)
    return jsonify(resultat), 200


@app.route("/reload", methods=["POST"])
def reload_faqs():
    """
    Re-génère les embeddings depuis la base de données.
    À appeler après avoir ajouté ou modifié des FAQs via l'admin dashboard.
    """
    try:
        from sentence_transformers import SentenceTransformer
        from db import get_connection
        import numpy as np

        model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, question FROM faqs ORDER BY id")
        faqs = cursor.fetchall()

        for faq_id, question in faqs:
            embedding = model.encode(question, normalize_embeddings=True)
            cursor.execute(
                "UPDATE faqs SET embedding = %s WHERE id = %s",
                (embedding, faq_id)
            )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": f"{len(faqs)} embeddings régénérés avec succès."}), 200

    except Exception as e:
        return jsonify({"erreur": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":  "ok",
        "moteur":  "pgvector",
        "modele":  "paraphrase-multilingual-MiniLM-L12-v2",
        "seuil":   engine.seuil
    }), 200


if __name__ == "__main__":
    print("[DÉMARRAGE] Chatbot Universitaire EMI — V3 pgvector")
    print("[DÉMARRAGE] Chargement du modèle sentence-transformers...")
    app.run(host="0.0.0.0", port=5000, debug=True)
