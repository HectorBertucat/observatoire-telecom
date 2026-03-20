# ADR-003 : Vector tiles PMTiles + MapLibre GL JS pour la cartographie

## Statut : Accepté (mars 2026)

## Contexte
Les géométries de couverture ARCEP sont extrêmement lourdes (~200k points par
MULTIPOLYGON, 1148 géométries, ~900 MB en DuckDB). Servir ces données au
navigateur pour affichage sur une carte web pose un problème de performance.

## Décision
Adopter l'architecture **vector tiles** :
1. **Tippecanoe** pré-génère un fichier **PMTiles** avec simplification par zoom (z4-z12)
2. **MapLibre GL JS** remplace Leaflet pour le rendu WebGL des vector tiles
3. La librairie **pmtiles.js** charge les tuiles depuis un fichier statique (pas de tile server)

## Options considérées

| Approche | Temps de chargement | Zoom progressif | Complexité |
|----------|-------------------|-----------------|------------|
| GeoJSON brut via API | ~minutes (timeout) | Non | Faible |
| GeoJSON simplifié statique | ~3s (2.7 MB) | Non | Faible |
| ST_Envelope (bounding boxes) | ~3s | Non, rectangles | Faible |
| Vector tiles (PMTiles) | ~instantané | Oui, détail progressif | Moyenne |
| Tile server (Martin, pg_tileserv) | ~instantané | Oui | Élevée |

## Conséquences
- **Positif** : zoom fluide avec détail progressif, rendu WebGL (GPU)
- **Positif** : PMTiles = fichier statique unique, pas de tile server à maintenir
- **Positif** : seules les tuiles visibles à l'écran sont chargées (~KB par requête)
- **Positif** : filtrage par opérateur instantané côté client (pas de re-fetch)
- **Négatif** : nécessite Tippecanoe (brew install tippecanoe) pour régénérer
- **Négatif** : fichier PMTiles de 74 MB à régénérer si les données changent
- **Leçon apprise** : Tippecanoe drop des features par défaut aux zooms bas
  (--coalesce-densest-as-needed). Utiliser --no-feature-limit --no-tile-size-limit
  pour les données de couverture où chaque polygone compte.

## Pipeline
```
DuckDB (Lambert-93) → ST_Simplify(500m) → ST_Transform(WGS84) → GeoJSON
    → Tippecanoe (z4-z12, --no-feature-limit) → PMTiles → MapLibre GL JS
```
