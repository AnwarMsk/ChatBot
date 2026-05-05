"""
Vectoriseur TF-IDF — implémentation maison.

Ce module construit la représentation vectorielle des questions de la FAQ.
L'objectif est pédagogique : chaque étape du calcul TF-IDF est écrite
explicitement, sans dépendre directement de scikit-learn pour la formule.

Rappel mathématique
───────────────────
Soit un corpus de N documents D = {d_1, ..., d_N}, et un vocabulaire V
composé des termes (mots) uniques apparaissant dans le corpus.

Pour un terme t et un document d :

    TF(t, d) = nombre d'occurrences de t dans d
                  / nombre total de termes dans d

    IDF(t)   = log( (1 + N) / (1 + DF(t)) ) + 1
               où DF(t) = nombre de documents contenant t
               (formule "smooth IDF", évite la division par zéro)

    TF-IDF(t, d) = TF(t, d) * IDF(t)

Chaque document est ensuite normalisé en norme L2 :
    v ← v / ||v||_2
    de sorte que tous les vecteurs aient une longueur unitaire.
    Cela rend la similarité cosinus équivalente à un simple produit scalaire.
"""

import math
from collections import Counter
import numpy as np


class TFIDFVectorizer:
    """
    Vectoriseur TF-IDF maison.

    Utilisation :
        vec = TFIDFVectorizer()
        X   = vec.fit_transform(["bonjour le monde", "le monde est grand"])
        Y   = vec.transform(["bonjour"])

    X et Y sont des matrices NumPy de forme (n_documents, taille_du_vocabulaire).
    """

    def __init__(self, sublinear_tf: bool = False, normalize: bool = True):
        """
        sublinear_tf : si True, remplace TF par 1 + log(TF) (atténue les
                       termes très fréquents). Désactivé par défaut.
        normalize    : si True, applique une normalisation L2 sur chaque vecteur.
                       Recommandé pour la similarité cosinus.
        """
        self.sublinear_tf = sublinear_tf
        self.normalize = normalize

        # Rempli par fit() :
        self.vocabulaire_ = {}   # dict {terme: index dans le vecteur}
        self.idf_ = None         # vecteur IDF (numpy array de taille |V|)

    # ─────────────────────────────────────────────────────────────────
    # Étape 1 — Construction du vocabulaire et calcul de l'IDF
    # ─────────────────────────────────────────────────────────────────
    def fit(self, documents: list):
        """
        Apprend le vocabulaire et calcule l'IDF à partir du corpus.

        documents : liste de chaînes déjà prétraitées (lemmatisées, sans
                    stop words, en minuscules).
        """
        if not documents:
            raise ValueError("Le corpus est vide, impossible d'apprendre le vocabulaire.")

        # 1.a  Tokenisation simple : on suppose que le texte est déjà nettoyé,
        #      on découpe juste sur les espaces.
        documents_tokens = [doc.split() for doc in documents]

        # 1.b  Vocabulaire = ensemble des mots uniques du corpus, trié pour
        #      garantir un ordre reproductible.
        termes_uniques = sorted({mot for tokens in documents_tokens for mot in tokens})
        self.vocabulaire_ = {terme: i for i, terme in enumerate(termes_uniques)}

        # 1.c  Document Frequency : DF(t) = nombre de documents contenant t.
        N = len(documents_tokens)
        df = np.zeros(len(self.vocabulaire_), dtype=np.float64)
        for tokens in documents_tokens:
            for terme in set(tokens):  # set() pour ne compter qu'une fois par doc
                df[self.vocabulaire_[terme]] += 1

        # 1.d  IDF lissé (smooth IDF) :
        #      IDF(t) = log((1 + N) / (1 + DF(t))) + 1
        #      Le "+1" final évite qu'un terme présent dans tous les
        #      documents ait un IDF nul (et donc un TF-IDF nul partout).
        self.idf_ = np.log((1.0 + N) / (1.0 + df)) + 1.0

        return self

    # ─────────────────────────────────────────────────────────────────
    # Étape 2 — Transformation d'un corpus en matrice TF-IDF
    # ─────────────────────────────────────────────────────────────────
    def transform(self, documents: list) -> np.ndarray:
        """
        Transforme une liste de documents en matrice TF-IDF.

        Retourne un tableau numpy de forme (len(documents), |vocabulaire|).
        Les mots inconnus (absents du vocabulaire appris dans fit) sont ignorés.
        """
        if self.idf_ is None:
            raise RuntimeError("Le vectoriseur n'a pas encore été entraîné. "
                               "Appelez fit() ou fit_transform() d'abord.")

        n_docs = len(documents)
        n_termes = len(self.vocabulaire_)
        matrice = np.zeros((n_docs, n_termes), dtype=np.float64)

        for i, doc in enumerate(documents):
            tokens = doc.split()
            if not tokens:
                continue

            # 2.a  TF brut : on compte les occurrences de chaque terme connu.
            compteur = Counter(tokens)
            longueur_doc = len(tokens)

            for terme, occurrences in compteur.items():
                if terme not in self.vocabulaire_:
                    continue  # mot inconnu ⇒ ignoré
                j = self.vocabulaire_[terme]

                # 2.b  TF normalisé : fréquence relative dans le document.
                tf = occurrences / longueur_doc

                # 2.c  Variante sublinéaire (atténue les très grandes fréquences).
                if self.sublinear_tf and tf > 0:
                    tf = 1.0 + math.log(tf)

                # 2.d  TF-IDF = TF × IDF
                matrice[i, j] = tf * self.idf_[j]

        # 2.e  Normalisation L2 ligne par ligne :
        #      après cette étape, chaque vecteur a une norme égale à 1
        #      (à condition qu'il ne soit pas entièrement nul).
        if self.normalize:
            normes = np.linalg.norm(matrice, axis=1, keepdims=True)
            normes[normes == 0] = 1.0  # protège la division par zéro
            matrice = matrice / normes

        return matrice

    # ─────────────────────────────────────────────────────────────────
    # Raccourci : fit puis transform sur le même corpus
    # ─────────────────────────────────────────────────────────────────
    def fit_transform(self, documents: list) -> np.ndarray:
        """Apprend le vocabulaire et renvoie directement la matrice TF-IDF."""
        self.fit(documents)
        return self.transform(documents)

    # ─────────────────────────────────────────────────────────────────
    # Utilitaires
    # ─────────────────────────────────────────────────────────────────
    def get_feature_names(self) -> list:
        """Renvoie la liste des termes du vocabulaire, dans l'ordre des colonnes."""
        return [terme for terme, _ in sorted(self.vocabulaire_.items(), key=lambda x: x[1])]