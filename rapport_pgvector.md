# Rapport Technique — Intégration pgvector pour la Recherche Sémantique

## 1. Introduction

Dans le cadre de l'évolution du chatbot universitaire de l'EMI (V3), nous avons intégré
la recherche sémantique vectorielle directement dans la base de données PostgreSQL grâce
à l'extension **pgvector**. Cette approche remplace le moteur TF-IDF de la V2 par un
système plus puissant, capable de comprendre le sens profond des questions posées par
les étudiants, indépendamment de la formulation exacte utilisée.

---

## 2. Fondements Théoriques

### 2.1 Les Embeddings (Représentations Vectorielles)

Un **embedding** est une représentation mathématique d'un texte sous forme d'un vecteur
de nombres réels dans un espace à haute dimension. Ce vecteur encode le **sens sémantique**
du texte : deux phrases proches sémantiquement auront des vecteurs proches dans cet espace.

**Exemple :**

```
"Comment obtenir une bourse ?"
        -> modèle sentence-transformers
[0.231, -0.814, 0.502, 0.103, -0.671, ..., 0.044]   <- 384 dimensions

"Je voudrais des informations sur les bourses étudiantes"
        -> modèle sentence-transformers
[0.219, -0.798, 0.489, 0.121, -0.658, ..., 0.051]   <- très proche du vecteur ci-dessus
```

### 2.2 La Similarité Cosinus

La **similarité cosinus** mesure l'angle entre deux vecteurs dans l'espace multidimensionnel.
Elle est définie par :

```
         A . B
cos(θ) = ---------
          |A| |B|
```

- **Score = 1** : vecteurs identiques (même sens)
- **Score = 0** : vecteurs orthogonaux (sens sans rapport)
- **Score = -1** : vecteurs opposés (sens contraire)

Dans notre système, un seuil de **0.4** est appliqué : toute FAQ avec un score cosinus
supérieur à 0.4 est considérée comme une correspondance valide.

### 2.3 Le Modèle sentence-transformers

Le modèle utilisé est **`paraphrase-multilingual-MiniLM-L12-v2`**, développé par
l'équipe de recherche de l'Université de Mannheim. Ses caractéristiques :

| Propriété | Valeur |
|---|---|
| Langues supportées | 50+ (dont le français, l'arabe, l'anglais) |
| Dimension des vecteurs | 384 |
| Taille du modèle | ~420 Mo |
| Architecture | MiniLM (12 couches Transformer distillées) |
| Tâche d'entraînement | Similarité de paraphrases multilingues |

Ce modèle est particulièrement adapté à notre contexte car il a été entraîné spécifiquement
pour la **détection de paraphrases**, ce qui correspond exactement à notre besoin :
trouver la FAQ dont la question correspond sémantiquement à la question de l'étudiant.

---

## 3. L'Extension pgvector

### 3.1 Présentation

**pgvector** est une extension open-source pour PostgreSQL qui ajoute :
- Un **type de données** `vector(n)` pour stocker des embeddings directement dans la BDD
- Des **opérateurs de distance** vectorielle
- Des **index spécialisés** (IVFFlat et HNSW) pour accélérer les recherches

### 3.2 Opérateurs de Distance

| Opérateur | Distance | Cas d'usage |
|---|---|---|
| `<->` | Euclidienne (L2) | Distance géométrique pure |
| `<=>` | **Cosinus** | Similarité sémantique (notre choix) |
| `<#>` | Produit scalaire | Vecteurs normalisés |

Nous utilisons l'opérateur `<=>` (cosinus) car il est invariant à la magnitude des
vecteurs et mesure uniquement la direction, ce qui est plus adapté à la comparaison
de textes sémantiques.

### 3.3 L'Index HNSW

Le **HNSW (Hierarchical Navigable Small World)** est un algorithme d'indexation pour
la recherche de voisins approximatifs (ANN - Approximate Nearest Neighbors).

**Principe de fonctionnement :**
- Construit un graphe multi-couches où chaque noeud représente un vecteur
- Les couches supérieures permettent une navigation rapide ("autoroutes")
- Les couches inférieures permettent une recherche fine ("rues locales")
- Complexité de recherche : O(log n) au lieu de O(n) pour une recherche linéaire

```sql
CREATE INDEX faqs_embedding_hnsw_idx
ON faqs
USING hnsw (embedding vector_cosine_ops);
```

---

## 4. Architecture Technique V3

### 4.1 Modèle de Données

La table `faqs` a été enrichie d'une colonne `embedding` :

```sql
ALTER TABLE faqs ADD COLUMN embedding vector(384);
```

### 4.2 Pipeline de Recherche

```
Question utilisateur (texte)
        |
        v
  sentence-transformers          encode() -> numpy array [384 floats]
  paraphrase-multilingual        normalize_embeddings=True
        |
        v
  PostgreSQL + pgvector          SELECT answer, 1-(embedding <=> %s) AS score
  Requête SQL cosinus            FROM faqs ORDER BY embedding <=> %s LIMIT 1
        |
        v
Réponse + score de confiance
```

### 4.3 Rôle des Composants

L'architecture est découpée en microservices pour séparer la logique d'orchestration de l'intelligence artificielle.

#### 1. Le Backend (Spring Boot) — L'Orchestrateur
Le backend Java agit comme une **API Gateway**. Il est le point d'entrée unique pour le frontend Angular et orchestre le système :
- **Routage et Sécurité :** Gère les règles CORS et l'accès sécurisé.
- **Délégation NLP :** Transmet la question de l'étudiant au microservice Flask.
- **Mécanisme de Secours (Fallback) :** Si Flask est indisponible ou lent (timeout), Spring Boot intercepte l'erreur et bascule silencieusement sur une recherche par mots-clés classique (V1) en interrogeant directement PostgreSQL.
- **Administration CRUD :** Fournit les routes REST pour l'interface administrateur (ajouter, modifier, supprimer des FAQs).

#### 2. Le Microservice NLP (Python / Flask) — Le Moteur Sémantique
Le rôle de Python est strictement limité au traitement du langage naturel (NLP). Il opère en deux temps :
- **Phase Setup (Une seule fois) :** Lit les FAQs, les convertit en vecteurs via le modèle `sentence-transformers`, et les sauvegarde dans la colonne `embedding` de PostgreSQL.
- **Phase Runtime (À chaque requête) :** Reçoit la question de Spring Boot, l'encode en vecteur numérique, et exécute la requête SQL de similarité cosinus dans PostgreSQL. Il sert uniquement de "traducteur" texte-vers-vecteur pour la base de données.

#### 3. Flux d'une Requête

```
[ Étudiant (Angular) ]
          │
          │ 1. POST /api/chatbot/ask
          ▼
[ Backend (Spring Boot) ] ──▶ 2. POST /ask ──▶ [ Flask NLP ]
          │                  (Recherche sémantique V3)
          │
          │ 3. Si Flask est en panne (Fallback) :
          ╰──▶ SELECT * FROM faqs ──▶ [ PostgreSQL ]
               (Recherche mots-clés V1)
```

### 4.4 Requête SQL de Recherche Vectorielle

```sql
SELECT answer,
       question,
       1 - (embedding <=> %s) AS score
FROM faqs
WHERE embedding IS NOT NULL
ORDER BY embedding <=> %s
LIMIT 1;
```

---

## 5. Mécanisme de Dégradation Gracieuse (Fallback)

Si le service Flask NLP est indisponible (arrêt, timeout, erreur réseau), le backend
Spring Boot bascule automatiquement en **mode dégradé V1** (recherche par mots-clés).

L'interface Angular affiche un badge d'avertissement amber sur les réponses en mode
dégradé, informant l'étudiant que la réponse provient du système de secours.

---

## 6. Comparaison des Approches

| Critère | V1 (Mots-clés) | V2 (TF-IDF) | V3 (pgvector) |
|---|---|---|---|
| Compréhension sémantique | Aucune | Partielle | Profonde |
| Gestion des synonymes | Non | Non | Oui |
| FAQs chargées en RAM | Oui | Oui | Non |
| Scalabilité | Faible | Limitée | Excellente (HNSW) |
| Index de recherche | Aucun | Aucun | HNSW O(log n) |
| Multilingue | Non | Non | Oui (50+ langues) |

---

## 7. Procédure de Mise en Oeuvre

### Étape 1 — Installation des dépendances

```bash
pip install sentence-transformers pgvector psycopg2-binary
```

### Étape 2 — Activation de pgvector sur la VM

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Étape 3 — Génération initiale des embeddings

```bash
python setup_pgvector.py
```

### Étape 4 — Test de l'API Flask

```http
POST http://localhost:5000/ask
Content-Type: application/json

{ "question": "Je voudrais savoir comment faire pour m'inscrire à l'université" }
```

Réponse attendue :

```json
{
  "reponse":          "La réinscription administrative se fait en ligne...",
  "score":            0.7821,
  "question_matchee": "Comment se réinscrire à l'université ?",
  "trouve":           true
}
```

---

## 8. Conclusion

L'intégration de pgvector représente une évolution significative du chatbot universitaire.
En déléguant la recherche sémantique directement à PostgreSQL, le système gagne en
scalabilité (l'index HNSW permet des recherches en O(log n)), en robustesse (pas de
données en RAM) et en qualité de réponse (compréhension des synonymes et des paraphrases).

Le modèle `paraphrase-multilingual-MiniLM-L12-v2` offre un excellent compromis entre
performance et légèreté pour un contexte universitaire francophone, tout en ouvrant
la porte à des questions posées en arabe ou en anglais par des étudiants internationaux.
