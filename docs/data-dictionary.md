# Data Dictionary — Observatoire Télécom

## Vue d'ensemble

Base DuckDB (`data/observatoire.duckdb`) avec extension spatial.
Coordonnées stockées en **Lambert-93 (EPSG:2154)**, reprojetées en WGS84 pour l'affichage.

## Tables

### ref_operators
Référentiel des opérateurs mobiles métropolitains.

| Colonne | Type | Description |
|---------|------|-------------|
| code | VARCHAR (PK) | Code interne : BYT, FREE, OF, SFR |
| name | VARCHAR | Nom complet : Bouygues Telecom, Free Mobile, Orange, SFR |
| color | VARCHAR | Couleur hex pour les visualisations |

> **Note** : les codes fichiers ARCEP diffèrent (BOUY, FREE, OF, SFR0).
> Le mapping est dans `src/observatoire/ingestion/downloader.py` (ARCEP_TO_DB_OPERATOR).

### ref_technologies
Référentiel des technologies réseau.

| Colonne | Type | Description |
|---------|------|-------------|
| code | VARCHAR (PK) | 2G, 3G, 4G, 5G |
| generation | INTEGER | Numéro de génération (2, 3, 4, 5) |
| description | VARCHAR | Ex: "LTE - Haut débit mobile" |

### raw_coverage
Couvertures théoriques ARCEP — données brutes géospatiales.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Auto-incrémenté (sequence coverage_seq) |
| quarter | VARCHAR | Trimestre ARCEP : ex "2025_T3" |
| operator_code | VARCHAR | Code opérateur (FK ref_operators.code) |
| technology | VARCHAR | 2G, 3G, 4G, 5G |
| usage | VARCHAR | Type d'usage : "data", "voix" |
| geometry | GEOMETRY | MULTIPOLYGON en Lambert-93 (EPSG:2154) |
| quality_level | INTEGER | Niveau de qualité (1-3), nullable |
| ingested_at | TIMESTAMP | Date d'ingestion |
| source_file | VARCHAR | Nom du fichier source (.gpkg) |

> **Volumétrie** : ~287 lignes par opérateur×technologie. Chaque géométrie contient
> ~120k-310k points. Total actuel : 1148 lignes (4 opérateurs × 4G).

### raw_antenna_sites
Sites d'antennes ANFR — pas encore peuplée.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Identifiant ANFR |
| operator | VARCHAR | Nom de l'opérateur |
| latitude | DOUBLE | Latitude WGS84 |
| longitude | DOUBLE | Longitude WGS84 |
| commune_code | VARCHAR | Code INSEE de la commune |
| commune_name | VARCHAR | Nom de la commune |
| department_code | VARCHAR | Code département |
| technology | VARCHAR | 2G, 3G, 4G, 5G |
| frequency_band | VARCHAR | Bande de fréquence |
| date_mise_en_service | DATE | Date de mise en service |
| geometry | GEOMETRY | Point |
| ingested_at | TIMESTAMP | Date d'ingestion |

### mart_coverage_by_commune
Table agrégée : couverture par commune — pas encore peuplée.

| Colonne | Type | Description |
|---------|------|-------------|
| commune_code | VARCHAR | Code INSEE |
| commune_name | VARCHAR | Nom de la commune |
| department_code | VARCHAR | Code département |
| operator_code | VARCHAR | Code opérateur |
| technology | VARCHAR | 2G, 3G, 4G, 5G |
| quarter | VARCHAR | Trimestre |
| coverage_pct | DOUBLE | % de surface couverte |
| population_covered | INTEGER | Population couverte |
| total_population | INTEGER | Population totale |
| antenna_count | INTEGER | Nombre d'antennes |
| updated_at | TIMESTAMP | Date de mise à jour |

## Sources de données

| Source | Format | Fréquence | Statut |
|--------|--------|-----------|--------|
| ARCEP — couvertures théoriques | GeoPackage (.gpkg.7z) | Trimestriel | Chargé (4G, 2025_T3) |
| ANFR — antennes-relais | CSV | Continu | Pas encore ingéré |
| INSEE — population | CSV / API | Variable | Pas encore ingéré |
