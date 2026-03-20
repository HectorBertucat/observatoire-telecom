# Observatoire Télécom France

## Contexte
Ce projet est un observatoire open-source de la couverture et de la qualité
des réseaux mobiles en France, basé sur les données ouvertes ARCEP/ANFR.

## Stack technique
- Python 3.12+ avec uv (gestionnaire de paquets)
- DuckDB avec extension spatial (base analytique)
- FastAPI (API REST)
- MCP SDK Python (serveur Model Context Protocol)
- pydantic-ai + anthropic SDK (agents IA)

## Conventions
- Code en anglais (noms de variables, fonctions, classes)
- Commentaires et docstrings en français
- Type hints obligatoires partout
- Tous les modèles de données utilisent Pydantic v2
- Requêtes SQL dans des fonctions dédiées (pas inline dans les handlers)
- Convention de nommage tables : raw_*, stg_*, mart_*, ref_*
- Tests avec pytest, fixtures dans conftest.py
- Linting : ruff (déjà configuré dans pyproject.toml)

## Structure
- src/observatoire/ : code source principal
- src/observatoire/ingestion/ : pipeline d'ingestion des données
- src/observatoire/db/ : couche données DuckDB
- src/observatoire/api/ : API REST FastAPI
- src/observatoire/mcp/ : serveur MCP
- src/observatoire/agent/ : agent d'analyse Claude
- tests/ : tests unitaires et d'intégration
- data/ : données locales (raw, processed, samples)

## Commandes courantes
- `make ingest` : lancer le pipeline d'ingestion
- `make serve` : lancer l'API en dev (uvicorn --reload)
- `make test` : lancer les tests
- `make lint` : vérifier le code avec ruff
- `make mcp` : lancer le serveur MCP

## Règles de sécurité
- Ne jamais commiter de clés API dans le code
- DuckDB est ouvert en read-only pour l'API
- Les données brutes ne sont jamais servies directement
