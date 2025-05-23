# 🧠 Greeum v0.6.0

<p align="center">
  <a href="../../README.md">🇰🇷 한국어</a> |
  <a href="README_EN.md">🇺🇸 English</a> |
  <a href="README_ZH.md">🇨🇳 中文</a> |
  <a href="README_JP.md">🇯🇵 日本語</a> |
  <a href="README_ES.md">🇪🇸 Español</a> |
  <a href="README_DE.md">🇩🇪 Deutsch</a> |
  <a href="README_FR.md">🇫🇷 Français</a>
</p>

Système de Gestion de Mémoire Indépendant des LLM Multilingue

## 📌 Aperçu

Greeum est un système de mémoire indépendant de LLM basé sur l'architecture RAG (Génération Augmentée par Récupération, Retrieval-Augmented Generation). Il implémente les composants clés de RAG, notamment le stockage et la récupération d'informations (block_manager.py), la gestion des mémoires connexes (cache_manager.py) et l'augmentation des prompts (prompt_wrapper.py) pour générer des réponses plus précises et contextuellement pertinentes.

**Greeum** (prononcé : gri-eum) est un **module de mémoire universel** qui peut se connecter à n'importe quel LLM (Large Language Model) et offre les fonctionnalités suivantes :
- Suivi à long terme des expressions, objectifs, émotions et intentions de l'utilisateur
- Rappel des souvenirs liés au contexte actuel
- Reconnaissance et traitement des expressions temporelles dans des environnements multilingues
- Fonctionne comme une "IA avec mémoire"

Le nom "Greeum" est inspiré du mot coréen "그리움" (nostalgie/réminiscence), capturant parfaitement l'essence du système de mémoire.

## 🔑 Fonctionnalités Principales

- **Mémoire à Long Terme de type Blockchain (LTM)** : Stockage de mémoire basé sur des blocs avec immuabilité
- **Mémoire à Court Terme basée sur TTL (STM)** : Gestion efficace des informations temporairement importantes
- **Pertinence Sémantique** : Système de rappel de mémoire basé sur des mots-clés/tags/vecteurs
- **Cache de Points de Passage** : Récupération automatique des souvenirs liés au contexte actuel
- **Compositeur de Prompts** : Génération automatique de prompts LLM avec des souvenirs pertinents
- **Raisonneur Temporel** : Reconnaissance avancée des expressions temporelles dans des environnements multilingues
- **Support Multilingue** : Détection et traitement automatique des langues pour le coréen, l'anglais, etc.
- **Protocole de Contrôle de Modèle** : Support d'intégration d'outils externes pour Cursor, Unity, Discord, etc. via le package séparé [GreeumMCP](https://github.com/DryRainEnt/GreeumMCP)

## ⚙️ Installation

1. Cloner le dépôt
   ```bash
   git clone https://github.com/DryRainEnt/Greeum.git
   cd Greeum
   ```

2. Installer les dépendances
   ```bash
   pip install -r requirements.txt
   ```

## 🧪 Utilisation

### Interface en Ligne de Commande

```bash
# Ajouter une mémoire à long terme
python cli/memory_cli.py add -c "J'ai commencé un nouveau projet et c'est vraiment passionnant"

# Rechercher des souvenirs par mots-clés
python cli/memory_cli.py search -k "projet,passionnant"

# Rechercher des souvenirs par expression temporelle
python cli/memory_cli.py search-time -q "Qu'ai-je fait il y a 3 jours ?" -l "fr"

# Ajouter une mémoire à court terme
python cli/memory_cli.py stm "Le temps est agréable aujourd'hui"

# Obtenir les mémoires à court terme
python cli/memory_cli.py get-stm

# Générer un prompt
python cli/memory_cli.py prompt -i "Comment avance le projet ?"
```

### Serveur REST API

```bash
# Exécuter le serveur API
python api/memory_api.py
```

Interface web : http://localhost:5000

Points d'accès API :
- GET `/api/v1/health` - Vérification de santé
- GET `/api/v1/blocks` - Lister les blocs
- POST `/api/v1/blocks` - Ajouter un bloc
- GET `/api/v1/search?keywords=keyword1,keyword2` - Recherche par mots-clés
- GET `/api/v1/search/time?query=yesterday&language=en` - Recherche par expression temporelle
- GET, POST, DELETE `/api/v1/stm` - Gérer les mémoires à court terme
- POST `/api/v1/prompt` - Générer un prompt
- GET `/api/v1/verify` - Vérifier l'intégrité de la blockchain

### Bibliothèque Python

```python
from greeum import BlockManager, STMManager, CacheManager, PromptWrapper
from greeum.text_utils import process_user_input
from greeum.temporal_reasoner import TemporalReasoner

# Traiter l'entrée utilisateur
user_input = "J'ai commencé un nouveau projet et c'est vraiment passionnant"
processed = process_user_input(user_input)

# Stocker la mémoire avec le gestionnaire de blocs
block_manager = BlockManager()
block = block_manager.add_block(
    context=processed["context"],
    keywords=processed["keywords"],
    tags=processed["tags"],
    embedding=processed["embedding"],
    importance=processed["importance"]
)

# Recherche basée sur le temps (multilingue)
temporal_reasoner = TemporalReasoner(db_manager=block_manager, default_language="auto")
time_query = "Qu'ai-je fait il y a 3 jours ?"
time_results = temporal_reasoner.search_by_time_reference(time_query)

# Générer un prompt
cache_manager = CacheManager(block_manager=block_manager)
prompt_wrapper = PromptWrapper(cache_manager=cache_manager)

user_question = "Comment avance le projet ?"
prompt = prompt_wrapper.compose_prompt(user_question)

# Passer au LLM
# llm_response = call_your_llm(prompt)
```

## 🧱 Architecture

```
greeum/
├── greeum/                # Bibliothèque principale
│   ├── block_manager.py    # Gestion de la mémoire à long terme
│   ├── stm_manager.py      # Gestion de la mémoire à court terme
│   ├── cache_manager.py    # Cache de points de passage
│   ├── prompt_wrapper.py   # Composition de prompts
│   ├── text_utils.py       # Utilitaires de traitement de texte
│   ├── temporal_reasoner.py # Raisonnement temporel
│   ├── embedding_models.py  # Intégration de modèles d'embedding
├── api/                   # Interface REST API
├── cli/                   # Outils en ligne de commande
├── data/                  # Répertoire de stockage de données
├── tests/                 # Suite de tests
```

## Règles de Gestion des Branches

- **main** : Branche de version stable
- **dev** : Branche de développement de fonctionnalités principales (fusionnée à main après développement et tests)
- **test-collect** : Branche de collecte de métriques de performance et de données de tests A/B

## 📊 Tests de Performance

Greeum effectue des tests de performance dans les domaines suivants :

### T-GEN-001 : Taux d'Augmentation de la Spécificité des Réponses
- Mesure de l'amélioration de la qualité des réponses lors de l'utilisation de la mémoire Greeum
- Confirmation d'une amélioration de qualité moyenne de 18,6%
- Augmentation de 4,2 inclusions d'informations spécifiques

### T-MEM-002 : Latence de Recherche de Mémoire
- Mesure de l'amélioration de la vitesse de recherche grâce au cache de points de passage
- Confirmation d'une amélioration de vitesse moyenne de 5,04 fois
- Jusqu'à 8,67 fois d'amélioration de vitesse pour plus de 1 000 blocs de mémoire

### T-API-001 : Efficacité des Appels API
- Mesure du taux de réduction des requêtes répétées grâce à la fourniture de contexte basée sur la mémoire
- Confirmation d'une réduction de 78,2% de la nécessité de requêtes répétées
- Effet de réduction des coûts en raison de la diminution des appels API

## 📊 Structure de Bloc de Mémoire

```json
{
  "block_index": 143,
  "timestamp": "2025-05-08T01:02:33",
  "context": "J'ai commencé un nouveau projet et c'est vraiment passionnant",
  "keywords": ["projet", "commencer", "passionnant"],
  "tags": ["positif", "début", "motivation"],
  "embedding": [0.131, 0.847, ...],
  "importance": 0.91,
  "hash": "...",
  "prev_hash": "..."
}
```

## 🔤 Langues Prises en Charge

Greeum prend en charge la reconnaissance d'expressions temporelles dans les langues suivantes :
- 🇰🇷 Coréen : Support de base pour les expressions temporelles coréennes (어제, 지난주, 3일 전, etc.)
- 🇺🇸 Anglais : Support complet pour les formats temporels en anglais (yesterday, 3 days ago, etc.)
- 🇫🇷 Français : Support pour les expressions temporelles en français (hier, il y a trois jours, etc.)
- 🌐 Détection automatique : Détecte automatiquement la langue et la traite en conséquence

## 🔍 Exemples de Raisonnement Temporel

```python
# Coréen
result = evaluate_temporal_query("3일 전에 뭐 했어?", language="ko")
# Valeur de retour : {detected: True, language: "ko", best_ref: {term: "3일 전"}}

# Anglais
result = evaluate_temporal_query("What did I do 3 days ago?", language="en")
# Valeur de retour : {detected: True, language: "en", best_ref: {term: "3 days ago"}}

# Français
result = evaluate_temporal_query("Qu'ai-je fait il y a 3 jours ?", language="fr")
# Valeur de retour : {detected: True, language: "fr", best_ref: {term: "il y a 3 jours"}}

# Détection automatique
result = evaluate_temporal_query("What happened yesterday?")
# Valeur de retour : {detected: True, language: "en", best_ref: {term: "yesterday"}}
```

## 🔧 Plans d'Expansion du Projet

- **Protocole de Contrôle de Modèle** : Consultez le dépôt [GreeumMCP](https://github.com/DryRainEnt/GreeumMCP) pour le support MCP - un package séparé qui permet à Greeum de se connecter à des outils comme Cursor, Unity, Discord, etc.
- **Support Multilingue Amélioré** : Support linguistique supplémentaire pour le japonais, le chinois, l'espagnol, etc.
- **Embeddings Améliorés** : Intégration de modèles d'embedding réels (par ex., sentence-transformers)
- **Extraction de Mots-clés Améliorée** : Implémentation d'extraction de mots-clés spécifique à la langue
- **Intégration Cloud** : Ajout de backends de base de données (SQLite, MongoDB, etc.)
- **Traitement Distribué** : Implémentation de traitement distribué pour la gestion de mémoire à grande échelle

## 🌐 Site Web

Visitez le site web : [greeum.app](https://greeum.app)

## 📄 Licence

Licence MIT

## 👥 Contribution

Toutes les contributions sont les bienvenues, y compris les rapports de bugs, les suggestions de fonctionnalités, les pull requests, etc. !

## 📱 Contact

Email : playtart@play-t.art 