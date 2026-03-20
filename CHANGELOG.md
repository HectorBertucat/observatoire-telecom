# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [Unreleased]

### Added
- Pipeline d'ingestion ARCEP : download async (httpx) → extract 7z → load GeoPackage
- Couche données DuckDB : schéma (raw_coverage, raw_antenna_sites, ref_operators,
  ref_technologies, mart_coverage_by_commune), connexion avec extension spatial
- API REST FastAPI : endpoints couverture, antennes, stats, health check, OpenAPI auto
- Serveur MCP (FastMCP) : 3 tools (get_coverage, compare_operators, get_antenna_density),
  3 resources (operators, technologies, stats), 2 prompts
- Agent d'analyse Claude : architecture hub-and-spoke avec coordinator + 3 sous-agents
  (fetcher, analyzer, reporter) via pydantic-ai
- Frontend dashboard : MapLibre GL JS + PMTiles vector tiles, Chart.js
- Vector tiles : Tippecanoe génère PMTiles (z4-z12) depuis GeoJSON simplifié
- Docker + docker-compose : API + Cloudflare Tunnel
- CI/CD : GitHub Actions (lint, test, typecheck)
- Documentation : CLAUDE.md, ADR, data dictionary, changelog
- Légende interactive sur la carte avec checkboxes par opérateur
- Données ANFR : 354k sites d'antennes (2G/3G/4G/5G, 4 opérateurs)
- Résolution des tuiles améliorée : simplification 250m au lieu de 500m
- Antennes ANFR affichées comme points sur la carte (z8+, 354k sites)
- PMTiles séparé pour les antennes avec clustering Tippecanoe (19 MB)
- Popup au clic sur antenne : opérateur, technologie, commune
- Dashboard stats enrichies : total sites, 4G, 5G, opérateurs
- Graphique stacked bars : sites d'antennes par opérateur × technologie
- API antennes : endpoints /antennas/ et /antennas/stats avec pagination/filtres
- README complet avec guide de démarrage, API, architecture
- Licence MIT
- 5 nouveaux tests API antennes (26 tests total)
- MCP tools refactorisés pour utiliser les données réelles (ANFR)
  - get_antenna_count, compare_operators, get_coverage_summary, search_antennas

### Fixed
- Reprojection Lambert-93 (EPSG:2154) → WGS84 (EPSG:4326) avec ST_FlipCoordinates
- Simplification géométrique : tolérance en mètres (5000m) au lieu de degrés
- Tippecanoe : --no-feature-limit pour éviter les zones vides au dézoom
- Tests API isolés avec DB temporaire pour éviter les conflits de lock DuckDB

### Performance
- GeoJSON pré-simplifié : 200k pts/geom → ~80 pts/geom (tolérance 5km)
- PMTiles vector tiles : chargement progressif, seules les tuiles visibles sont servies
- Payload total : 2.7 MB GeoJSON statique (vs 900 MB brut)
