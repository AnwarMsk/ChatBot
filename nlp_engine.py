"""
Moteur NLP du chatbot universitaire.

Le moteur enchaîne trois étapes :
    1. Prétraitement linguistique (spaCy) : minuscules, suppression des
       stop words, ponctuation et lettres isolées, lemmatisation.
    2. Vectorisation TF-IDF : chaque question devient un vecteur numérique.
       (Voir vectorizer.py pour le détail des formules.)
    3. Similarité cosinus : on compare la question utilisateur à toutes
       les FAQ et on garde la plus proche, à condition que le score
       dépasse un seuil de confiance.
       (Voir similarity.py pour le détail du calcul.)
"""

import spacy
import numpy as np

from vectorizer import TFIDFVectorizer
from similarity import cosine_similarity_matrix

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

    - Met en minuscules
    - Supprime la ponctuation, les espaces et les stop words
    - Réduit chaque mot à sa forme de base (lemme)
    - Filtre les tokens d'un seul caractère
    """
    if nlp is None:
        return text.lower()

    doc = nlp(text.lower())
    tokens = [
        token.lemma_
        for token in doc
        if not token.is_stop
        and not token.is_punct
        and not token.is_space
        and len(token.text) > 1
    ]
    return " ".join(tokens)


class NLPEngine:
    """
    Moteur de recherche sémantique basé sur TF-IDF + similarité cosinus.

    Fonctionnement
    ──────────────
    1. On charge toutes les questions de la FAQ depuis la BDD.
    2. On les prétraite (preprocess) puis on les vectorise (TF-IDF).
    3. Quand une question utilisateur arrive, on lui applique le même
       prétraitement, puis on la projette dans l'espace TF-IDF.
    4. On calcule la similarité cosinus entre cette question et toutes
       les FAQ ; on retourne la plus proche si le score dépasse le seuil.
    """

    def __init__(self, seuil_similarite: float = 0.3, sublinear_tf: bool = False):
        """
        seuil_similarite : score minimum (entre 0 et 1) pour qu'une FAQ
                           soit considérée comme une réponse valable.
                           Plus le seuil est élevé, plus le chatbot est strict.
        sublinear_tf     : transmis au vectoriseur (voir vectorizer.py).
        """
        self.seuil = seuil_similarite
        self.vectorizer = TFIDFVectorizer(sublinear_tf=sublinear_tf, normalize=True)
        self.faqs = []
        self.questions_vec = None  # matrice TF-IDF des questions de la FAQ

    # ─────────────────────────────────────────────────────────────
    # Chargement et vectorisation des FAQ
    # ─────────────────────────────────────────────────────────────
    def charger_faqs(self, faqs: list):
        """
        Apprend le vocabulaire et vectorise toutes les questions.

        À appeler une fois au démarrage du serveur (et après chaque mise
        à jour de la base via /reload).

        faqs : liste de dicts [{question, reponse, ...}, ...]
        """
        if not faqs:
            print("[AVERTISSEMENT] Aucune FAQ chargée.")
            self.faqs = []
            self.questions_vec = None
            return

        self.faqs = faqs

        # Étape 1 : prétraitement linguistique de chaque question.
        questions_traitees = [preprocess(faq["question"]) for faq in faqs]

        # Étape 2 : apprentissage du vocabulaire + calcul de la matrice TF-IDF.
        # fit_transform fait à la fois fit() (vocabulaire + IDF) et transform().
        self.questions_vec = self.vectorizer.fit_transform(questions_traitees)

        print(
            f"[NLP] {len(faqs)} FAQs vectorisées — "
            f"vocabulaire : {len(self.vectorizer.vocabulaire_)} termes, "
            f"matrice : {self.questions_vec.shape}."
        )

    # ─────────────────────────────────────────────────────────────
    # Recherche de la meilleure réponse
    # ─────────────────────────────────────────────────────────────
    def trouver_reponse(self, question_utilisateur: str) -> dict:
        """
        Renvoie la meilleure réponse pour une question donnée.

        Retour : dict avec
            - reponse          : texte de la réponse (ou message d'échec)
            - score            : similarité cosinus de la meilleure FAQ
            - question_matchee : question de la FAQ choisie (ou None)
            - trouve           : booléen, True si score >= seuil
        """
        if self.questions_vec is None or not self.faqs:
            return self._reponse_erreur(
                "Le moteur NLP n'est pas encore initialisé."
            )

        # 1. Prétraitement de la question utilisateur (même pipeline que la FAQ).
        question_traitee = preprocess(question_utilisateur)

        if not question_traitee:
            return self._reponse_erreur(
                "Votre question ne contient pas de mots significatifs."
            )

        # 2. Projection dans l'espace TF-IDF appris sur la FAQ.
        try:
            question_vec = self.vectorizer.transform([question_traitee])
        except Exception as e:
            print(f"[ERREUR] Vectorisation impossible : {e}")
            return self._reponse_erreur("Je n'ai pas pu traiter votre question.")

        # 3. Similarité cosinus avec toutes les FAQ.
        scores = cosine_similarity_matrix(question_vec[0], self.questions_vec)

        # 4. Sélection de la FAQ la plus proche.
        meilleur_index = int(np.argmax(scores))
        meilleur_score = float(scores[meilleur_index])

        if meilleur_score >= self.seuil:
            faq_choisie = self.faqs[meilleur_index]
            return {
                "reponse": faq_choisie["reponse"],
                "score": round(meilleur_score, 4),
                "question_matchee": faq_choisie["question"],
                "trouve": True,
            }

        return {
            "reponse": (
                "Je n'ai pas trouvé de réponse à votre question. "
                "Veuillez contacter la scolarité."
            ),
            "score": round(meilleur_score, 4),
            "question_matchee": None,
            "trouve": False,
        }

    # ─────────────────────────────────────────────────────────────
    # Outils internes
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    def _reponse_erreur(message: str) -> dict:
        return {
            "reponse": message,
            "score": 0,
            "question_matchee": None,
            "trouve": False,
        }
