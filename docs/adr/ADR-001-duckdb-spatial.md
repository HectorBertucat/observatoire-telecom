# ADR-001 : DuckDB avec extension spatial comme base analytique

## Statut : Accepté (mars 2026)

## Contexte
Le projet ingère des données géospatiales ARCEP (GeoPackage, ~200k points par
géométrie MULTIPOLYGON) et doit les stocker, les requêter, et les transformer.
Alternatives considérées : PostgreSQL + PostGIS, ClickHouse, SQLite + SpatiaLite.

## Décision
Utiliser **DuckDB** avec l'extension **spatial** comme base analytique unique.

## Options considérées

| Critère | DuckDB | PostgreSQL + PostGIS | ClickHouse |
|---------|--------|---------------------|------------|
| Installation | Zéro (lib Python) | Serveur à maintenir | Serveur lourd |
| RAM | ~200 MB | ~500 MB | ~2 GB min |
| Geospatial | Extension spatial (GDAL intégré) | PostGIS (excellent) | Limité |
| Lecture GeoPackage | ST_Read() natif | Nécessite ogr2ogr | Non supporté |
| Portabilité | Un fichier .duckdb | Un serveur | Un cluster |
| OLAP | Excellent | Moyen | Excellent |

## Conséquences
- **Positif** : développement 100% local, pas de serveur, ST_Read() lit directement
  les .gpkg ARCEP, fichier unique portable
- **Positif** : extension spatial inclut GDAL → pas d'outil externe pour les conversions
- **Négatif** : pas de concurrence multi-writer (un seul process écrit à la fois)
- **Négatif** : les données sont en Lambert-93 (EPSG:2154), nécessite ST_Transform
  pour l'affichage web (EPSG:4326)
- **Leçon apprise** : la tolérance de ST_Simplify est en unités du CRS source (mètres
  pour Lambert-93), pas en degrés — 0.1m ≠ 0.1° de simplification
