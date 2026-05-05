from flask import Flask, request, jsonify
from nlp_engine import NLPEngine
from db import get_all_faqs

app = Flask(__name__)

engine = NLPEngine(seuil_similarite=0.3)


def initialiser_moteur():
    print("[DÉMARRAGE] Chargement des FAQs depuis Oracle...")
    try:
        faqs = get_all_faqs()
        engine.charger_faqs(faqs)
        print("[DÉMARRAGE] Moteur NLP prêt.")
    except Exception as e:
        print(f"[ERREUR] Impossible de charger les FAQs : {e}")
        print("[INFO] Utilisation des FAQs de secours (mode hors-ligne).")
        _charger_faqs_fallback()


def _charger_faqs_fallback():
    import json
    try:
        with open("data/faq_universitaire.json", "r", encoding="utf-8") as f:
            faqs = json.load(f)
        engine.charger_faqs(faqs)
        print("[INFO] FAQs chargées depuis le fichier JSON local.")
    except Exception as e:
        print(f"[ERREUR] Impossible de charger le fichier JSON : {e}")


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
    try:
        faqs = get_all_faqs()
        engine.charger_faqs(faqs)
        return jsonify({"message": f"{len(faqs)} FAQs rechargées avec succès."}), 200
    except Exception as e:
        return jsonify({"erreur": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    nb_faqs = len(engine.faqs)
    return jsonify({
        "status": "ok",
        "faqs_chargees": nb_faqs,
        "moteur_pret": nb_faqs > 0
    }), 200

if __name__ == "__main__":
    initialiser_moteur()
    app.run(host="0.0.0.0", port=5000, debug=True)
