"""
Calcul de la similarité cosinus — implémentation maison.

Définition
──────────
Pour deux vecteurs u et v de même dimension, la similarité cosinus est :

                    u · v
    cos(u, v) = ─────────────────
                ‖u‖₂ · ‖v‖₂

où :
    u · v   est le produit scalaire (somme des u_i × v_i)
    ‖x‖₂    est la norme euclidienne (sqrt(somme des x_i²))

Propriétés utiles :
    - cos(u, v) ∈ [-1, 1] en général, et ∈ [0, 1] pour des vecteurs TF-IDF
      (les composantes sont positives ou nulles).
    - 1  ⇒ vecteurs identiques en direction (questions très similaires)
    - 0  ⇒ vecteurs orthogonaux (aucun mot en commun)
    - Si les vecteurs sont déjà normalisés en L2, cos(u, v) = u · v.
"""

import numpy as np


def cosine_similarity_pair(u: np.ndarray, v: np.ndarray) -> float:
    """
    Similarité cosinus entre deux vecteurs.

    Renvoie un flottant dans [-1, 1] (ou [0, 1] pour des vecteurs TF-IDF).
    Si l'un des deux vecteurs est nul, renvoie 0 par convention.
    """
    u = np.asarray(u, dtype=np.float64).ravel()
    v = np.asarray(v, dtype=np.float64).ravel()

    if u.shape != v.shape:
        raise ValueError(
            f"Dimensions incompatibles : u={u.shape}, v={v.shape}"
        )

    produit_scalaire = float(np.dot(u, v))
    norme_u = float(np.linalg.norm(u))
    norme_v = float(np.linalg.norm(v))

    if norme_u == 0.0 or norme_v == 0.0:
        return 0.0

    return produit_scalaire / (norme_u * norme_v)


def cosine_similarity_matrix(vecteur: np.ndarray, matrice: np.ndarray) -> np.ndarray:
    """
    Similarité cosinus entre un vecteur et chaque ligne d'une matrice.

    Paramètres
    ──────────
    vecteur  : tableau de forme (d,) ou (1, d)
    matrice  : tableau de forme (n, d) — n documents, d dimensions

    Retour
    ──────
    Tableau de forme (n,) contenant les n scores de similarité.

    Implémentation vectorisée pour éviter une boucle Python lente :
        scores[i] = (vecteur · matrice[i]) / (‖vecteur‖ · ‖matrice[i]‖)
    """
    vecteur = np.asarray(vecteur, dtype=np.float64).ravel()
    matrice = np.asarray(matrice, dtype=np.float64)

    if matrice.ndim != 2 or matrice.shape[1] != vecteur.shape[0]:
        raise ValueError(
            f"Dimensions incompatibles : vecteur={vecteur.shape}, "
            f"matrice={matrice.shape}"
        )

    # Produit scalaire entre vecteur et chaque ligne de matrice → forme (n,)
    produits = matrice @ vecteur

    # Normes euclidiennes
    norme_v = np.linalg.norm(vecteur)
    normes_M = np.linalg.norm(matrice, axis=1)

    # Si la requête est nulle, tous les scores sont nuls.
    if norme_v == 0.0:
        return np.zeros(matrice.shape[0], dtype=np.float64)

    # Pour les lignes nulles de la matrice, on évite la division par zéro :
    # on les remplace temporairement par 1, le produit scalaire correspondant
    # vaut déjà zéro donc le score final reste zéro.
    denom = normes_M * norme_v
    denom_safe = np.where(denom == 0.0, 1.0, denom)

    scores = produits / denom_safe
    scores[denom == 0.0] = 0.0
    return scores
