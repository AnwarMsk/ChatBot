import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# ──────────────────────────────────────────────────────────────────
# Chargement du modèle spaCy (français)
# À installer : python -m spacy download fr_core_news_sm
# ──────────────────────────────────────────────────────────────────
try:
    nlp = spacy.load("fr_core_news_sm")
except OSError:
    print("[AVERTISSEMENT] Modèle spaCy 'fr_core_news_sm' non trouvé.")
    print("Lancez : python -m spacy download fr_core_news_sm")
    nlp = None


def preprocess(text: str) -> str:
    """
    Nettoie et lemmatise un texte avec spaCy.
    Ex: "Comment obtenir mes résultats ?" → "comment obtenir résultat"
    
    - Supprime la ponctuation et les stop words
    - Réduit chaque mot à sa forme de base (lemme)
    """
    if nlp is None:
        return text.lower()  # fallback si spaCy non disponible

    doc = nlp(text.lower())
    tokens = [
        token.lemma_
        for token in doc
        if not token.is_stop        # supprime "le", "de", "est"...
        and not token.is_punct      # supprime "?", "!", ","...
        and not token.is_space      # supprime les espaces
        and len(token.text) > 1     # supprime les lettres isolées
    ]
    return " ".join(tokens)


class NLPEngine:
    """
    Moteur de recherche sémantique basé sur TF-IDF.
    
    Fonctionnement :
    1. On charge toutes les questions de la FAQ depuis la BDD
    2. On les vectorise avec TF-IDF (représentation mathématique)
    3. Quand une question arrive, on la vectorise aussi
    4. On calcule la similarité cosinus entre la question et toutes les FAQ
    5. On retourne la réponse la plus proche si le score dépasse un seuil
    """

    def __init__(self, seuil_similarite: float = 0.3):
        """
        seuil_similarite : score minimum pour considérer une réponse valide (0 à 1)
        Plus le seuil est élevé, plus le chatbot sera "strict" dans ses réponses.
        """
        self.seuil = seuil_similarite
        self.vectorizer = TfidfVectorizer()
        self.faqs = []           # liste des FAQs [{keyword, question, reponse}]
        self.questions_vec = None  # matrice TF-IDF des questions

    def charger_faqs(self, faqs: list):
        """
        Charge et vectorise les FAQs.
        Appeler cette méthode au démarrage du serveur.
        
        faqs : liste de dicts [{keyword, question, reponse}, ...]
        """
        if not faqs:
            print("[AVERTISSEMENT] Aucune FAQ chargée.")
            return

        self.faqs = faqs

        # Préprocessing de toutes les questions
        questions_traitees = [preprocess(faq["question"]) for faq in faqs]

        # Vectorisation TF-IDF
        # Chaque question devient un vecteur numérique
        self.questions_vec = self.vectorizer.fit_transform(questions_traitees)

        print(f"[NLP] {len(faqs)} FAQs chargées et vectorisées.")

    def trouver_reponse(self, question_utilisateur: str) -> dict:
        """
        Trouve la meilleure réponse à la question de l'utilisateur.
        
        Retourne un dict :
        {
            "reponse": "...",
            "score": 0.85,        # degré de confiance (0 à 1)
            "question_matchee": "...",
            "trouve": True/False
        }
        """
        if self.questions_vec is None or not self.faqs:
            return {
                "reponse": "Le moteur NLP n'est pas encore initialisé.",
                "score": 0,
                "question_matchee": None,
                "trouve": False
            }

        # Préprocessing de la question utilisateur
        question_traitee = preprocess(question_utilisateur)

        # Vectorisation de la question utilisateur
        try:
            question_vec = self.vectorizer.transform([question_traitee])
        except Exception:
            return {
                "reponse": "Je n'ai pas pu traiter votre question.",
                "score": 0,
                "question_matchee": None,
                "trouve": False
            }

        # Calcul des similarités cosinus avec toutes les FAQs
        scores = cosine_similarity(question_vec, self.questions_vec).flatten()

        # Index de la FAQ la plus similaire
        meilleur_index = int(np.argmax(scores))
        meilleur_score = float(scores[meilleur_index])

        if meilleur_score >= self.seuil:
            faq_choisie = self.faqs[meilleur_index]
            return {
                "reponse": faq_choisie["reponse"],
                "score": round(meilleur_score, 4),
                "question_matchee": faq_choisie["question"],
                "trouve": True
            }
        else:
            return {
                "reponse": "Je n'ai pas trouvé de réponse à votre question. Veuillez contacter la scolarité.",
                "score": round(meilleur_score, 4),
                "question_matchee": None,
                "trouve": False
            }
