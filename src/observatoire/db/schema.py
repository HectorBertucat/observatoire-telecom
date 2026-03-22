"""Définition du schéma de la base de données."""

import duckdb


def create_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Crée toutes les tables du schéma."""

    # Table de référence des opérateurs
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ref_operators (
            code VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL,
            color VARCHAR
        )
    """)

    # Table de référence des technologies
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ref_technologies (
            code VARCHAR PRIMARY KEY,
            generation INTEGER,
            description VARCHAR
        )
    """)

    # Couverture théorique (données géospatiales ARCEP)
    conn.execute("CREATE SEQUENCE IF NOT EXISTS coverage_seq START 1")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw_coverage (
            id INTEGER DEFAULT nextval('coverage_seq'),
            quarter VARCHAR NOT NULL,
            operator_code VARCHAR NOT NULL,
            technology VARCHAR NOT NULL,
            usage VARCHAR NOT NULL,
            geometry GEOMETRY,
            quality_level INTEGER,
            ingested_at TIMESTAMP DEFAULT current_timestamp,
            source_file VARCHAR
        )
    """)

    # Sites d'antennes ANFR
    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw_antenna_sites (
            id INTEGER,
            operator VARCHAR,
            latitude DOUBLE,
            longitude DOUBLE,
            commune_code VARCHAR,
            commune_name VARCHAR,
            department_code VARCHAR,
            technology VARCHAR,
            frequency_band VARCHAR,
            date_mise_en_service DATE,
            geometry GEOMETRY,
            ingested_at TIMESTAMP DEFAULT current_timestamp
        )
    """)

    # Lignes ferroviaires RFN (SNCF Open Data)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ref_railway_lines (
            line_id VARCHAR,
            line_name VARCHAR,
            geometry GEOMETRY,
            length_km DOUBLE,
            ingested_at TIMESTAMP DEFAULT current_timestamp
        )
    """)

    # Gares voyageurs (SNCF Open Data)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ref_railway_stations (
            station_id VARCHAR,
            station_name VARCHAR,
            line_code VARCHAR,
            commune VARCHAR,
            department VARCHAR,
            latitude DOUBLE,
            longitude DOUBLE,
            geometry GEOMETRY,
            ingested_at TIMESTAMP DEFAULT current_timestamp
        )
    """)

    # Couverture simplifiée (pré-calculée pour les analyses spatiales rapides)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stg_coverage_simplified (
            operator_code VARCHAR NOT NULL,
            technology VARCHAR NOT NULL,
            geometry GEOMETRY,
            bbox_xmin DOUBLE,
            bbox_ymin DOUBLE,
            bbox_xmax DOUBLE,
            bbox_ymax DOUBLE
        )
    """)

    # Table agrégée : couverture par commune
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mart_coverage_by_commune (
            commune_code VARCHAR,
            commune_name VARCHAR,
            department_code VARCHAR,
            operator_code VARCHAR,
            technology VARCHAR,
            quarter VARCHAR,
            coverage_pct DOUBLE,
            population_covered INTEGER,
            total_population INTEGER,
            antenna_count INTEGER,
            updated_at TIMESTAMP DEFAULT current_timestamp
        )
    """)


def seed_reference_data(conn: duckdb.DuckDBPyConnection) -> None:
    """Insère les données de référence (opérateurs, technologies)."""
    conn.execute("""
        INSERT OR IGNORE INTO ref_operators (code, name, color) VALUES
            ('BYT', 'Bouygues Telecom', '#003DA5'),
            ('FREE', 'Free Mobile', '#CD1719'),
            ('OF', 'Orange', '#FF6600'),
            ('SFR', 'SFR', '#E4002B')
    """)

    conn.execute("""
        INSERT OR IGNORE INTO ref_technologies (code, generation, description) VALUES
            ('2G', 2, 'GSM - Voix et SMS'),
            ('3G', 3, 'UMTS - Internet mobile basique'),
            ('4G', 4, 'LTE - Haut débit mobile'),
            ('5G', 5, '5G NR - Très haut débit mobile')
    """)
