# Observatoire Télécom France

## Contexte
Observatoire open-source de la couverture et de la qualité des réseaux mobiles
en France, basé sur les données ouvertes ARCEP/ANFR. Side-project data engineering
+ préparation certification Claude Certified Architect (CCA-F).

## Stack technique
- Python 3.12+ avec uv (gestionnaire de paquets)
- DuckDB avec extension spatial (base analytique, données en Lambert-93 / EPSG:2154)
- FastAPI (API REST)
- MCP SDK Python — FastMCP (serveur Model Context Protocol)
- pydantic-ai + anthropic SDK (agents IA)
- MapLibre GL JS + PMTiles (carte vector tiles, remplace Leaflet)
- Tippecanoe (génération des vector tiles)
- Chart.js (graphiques)

## Conventions
- Code en anglais (noms de variables, fonctions, classes)
- Commentaires et docstrings en français
- Type hints obligatoires partout
- Tous les modèles de données utilisent Pydantic v2
- Requêtes SQL dans des fonctions dédiées (pas inline dans les handlers)
- Convention de nommage tables : raw_*, stg_*, mart_*, ref_*
- Tests avec pytest, fixtures dans conftest.py
- Linting : ruff (déjà configuré dans pyproject.toml)
- Commits : conventional commits (feat:, fix:, perf:, docs:, etc.)

## Structure
- src/observatoire/ : code source principal
- src/observatoire/ingestion/ : pipeline d'ingestion (downloader, extractor, loader)
- src/observatoire/db/ : couche données DuckDB (connection, schema, queries, simplify)
- src/observatoire/api/ : API REST FastAPI (routers, schemas, deps)
- src/observatoire/mcp/ : serveur MCP (tools, resources, prompts)
- src/observatoire/agent/ : agent d'analyse Claude (coordinator, sub_agents)
- frontend/ : dashboard web (HTML/JS/CSS, MapLibre, Chart.js)
- scripts/ : pipeline (run_full_pipeline.py, generate_tiles.py)
- tests/ : tests unitaires et d'intégration (21 tests)
- data/ : données locales (gitignored sauf samples/)
- docs/ : documentation projet (ADR, data dictionary)

## Commandes courantes
- `make serve` : lancer l'API en dev (uvicorn --reload) → http://localhost:8000
- `make test` : lancer les tests (pytest)
- `make lint` : vérifier le code (ruff check + format)
- `make format` : formater le code automatiquement
- `make mcp` : lancer le serveur MCP
- `make seed` : générer des données de test (sans téléchargement)
- `make tiles` : régénérer les vector tiles PMTiles
- `uv run python scripts/run_full_pipeline.py [operators...]` : pipeline d'ingestion complète

## Pipeline de données
1. Download : httpx async depuis data.arcep.fr → data/raw/
2. Extract : 7z → data/processed/ (.gpkg GeoPackage)
3. Load : ST_Read() DuckDB → table raw_coverage (EPSG:2154)
4. Simplify : ST_Simplify(geom, 500m) + ST_Transform → GeoJSON (EPSG:4326)
5. Tiles : Tippecanoe → PMTiles (z4-z12) → data/tiles/

## Données chargées (état actuel)
- 4 opérateurs : Orange (OF), Bouygues (BYT), Free (FREE), SFR (SFR)
- **raw_coverage** : 1148 géométries MULTIPOLYGON (4G, trimestre 2025_T3)
  - Codes fichiers ARCEP : BOUY, FREE, OF, SFR0 (≠ codes DB : BYT, FREE, OF, SFR)
  - Coordonnées en Lambert-93 (EPSG:2154)
- **raw_antenna_sites** : 354k sites d'antennes ANFR (2G/3G/4G/5G)
  - Source : data.gouv.fr, dataset "installations radioélectriques > 5 watts"
  - ADM_ID ANFR → opérateur : 23=OF, 6=BYT, 240=FREE, 137=SFR
  - Coordonnées en WGS84 (converties depuis DMS)
  - commune_code = COM_CD_INSEE (code INSEE), department_code = 2 premiers chiffres
  - Systèmes : GSM%=2G, UMTS%=3G, LTE%=4G, 5G NR%=5G
- **PMTiles** : coverage.pmtiles (141 MB, z4-z12) + antennas.pmtiles (19 MB, z7-z14)
- **5 MCP tools** : get_antenna_count, compare_operators, get_coverage_summary,
  search_antennas, find_nearby_antennas

## Règles de sécurité
- Ne jamais commiter de clés API dans le code
- DuckDB est ouvert en read-only pour l'API
- Les données brutes ne sont jamais servies directement (trop lourdes, ~200k pts/geom)
- Pas de innerHTML dans le frontend (DOM API uniquement)

## Documentation du projet
Le projet maintient une documentation vivante qui DOIT être mise à jour :
- **CHANGELOG.md** : mis à jour à chaque feature/fix (format Keep a Changelog)
- **docs/adr/** : un ADR par décision architecturale majeure
- **docs/data-dictionary.md** : schéma des tables DuckDB

**IMPORTANT — Règle de maintenance documentaire :**
Après chaque modification significative (nouvelle feature, fix important, changement
d'architecture), mettre à jour :
1. CHANGELOG.md → ajouter l'entrée dans [Unreleased]
2. docs/adr/ → créer un ADR si c'est une décision architecturale
3. docs/data-dictionary.md → si le schéma DB change
4. Ce fichier (CLAUDE.md) → si la stack, structure, ou état du projet change
