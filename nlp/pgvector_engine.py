"""
pgvector_engine.py — Moteur de recherche sémantique V3 basé sur pgvector.

Architecture :
    1. Le modèle sentence-transformers encode la question de l'utilisateur
       en un vecteur de 384 dimensions.
    2. PostgreSQL exécute une requête de similarité cosinus entre ce vecteur
       et tous les embeddings pré-calculés dans la table faqs.
    3. La FAQ avec le score le plus élevé est retournée si elle dépasse le seuil.

Avantages par rapport au TF-IDF (V2) :
    - Compréhension sémantique profonde (synonymes, paraphrases)
    - Pas de chargement en mémoire de toutes les FAQs
    - La recherche est faite directement en SQL (scalable)
    - Index HNSW dans PostgreSQL pour des recherches ultra-rapides
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from db import search_by_vector

# Modèle multilingue — supporte le français, l'arabe, l'anglais et 47 autres langues
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


class PgVectorEngine:
    """
    Moteur de recherche sémantique qui délègue la recherche à PostgreSQL via pgvector.

    Contrairement au NLPEngine (TF-IDF), ce moteur :
    - Ne charge pas les FAQs en mémoire au démarrage
    - Encode uniquement la question de l'utilisateur au moment de la requête
    - Interroge la base de données pour trouver la réponse la plus proche
    """

    def __init__(self, seuil_similarite: float = 0.4):
        """
        Args:
            seuil_similarite: Score cosinus minimum pour accepter une réponse (0 à 1).
                              0.4 = tolérant (plus de réponses retournées)
                              0.7 = strict (seulement les très bonnes correspondances)
        """
        self.seuil = seuil_similarite
        print(f"[PgVectorEngine] Chargement du modèle '{MODEL_NAME}'...")
        self.model = SentenceTransformer(MODEL_NAME)
        print(f"[PgVectorEngine] Modèle prêt. Seuil de similarité : {self.seuil}")

    def trouver_reponse(self, question_utilisateur: str) -> dict:
        """
        Trouve la réponse la plus sémantiquement proche de la question.

        Pipeline :
            question (texte) → embedding (numpy array) → SQL cosine search → réponse

        Returns:
            {
                "reponse":          "La bibliothèque est ouverte...",
                "score":            0.8412,
                "question_matchee": "Quels sont les horaires de la bibliothèque ?",
                "trouve":           True
            }
        """
        # Étape 1 : Encoder la question de l'utilisateur
        # normalize_embeddings=True garantit des vecteurs unitaires (requis pour cosinus)
        embedding: np.ndarray = self.model.encode(
            question_utilisateur,
            normalize_embeddings=True
        )

        # Étape 2 : Recherche par similarité cosinus dans PostgreSQL
        resultat = search_by_vector(embedding, seuil=self.seuil)

        if resultat:
            return {
                "reponse":          resultat["answer"],
                "score":            resultat["score"],
                "question_matchee": resultat["question"],
                "trouve":           True
            }
        else:
            return {
                "reponse":          "Je n'ai pas trouvé de réponse à votre question. Veuillez contacter la scolarité de l'EMI.",
                "score":            0.0,
                "question_matchee": None,
                "trouve":           False
            }
