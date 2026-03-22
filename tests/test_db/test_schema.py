"""Tests pour le schéma de la base de données."""

from observatoire.db.schema import create_schema, seed_reference_data


def test_create_schema_creates_all_tables(db_conn):
    """Vérifie que toutes les tables sont créées."""
    create_schema(db_conn)

    tables = [row[0] for row in db_conn.execute("SHOW TABLES").fetchall()]
    expected = [
        "mart_coverage_by_commune",
        "raw_antenna_sites",
        "raw_coverage",
        "ref_operators",
        "ref_railway_lines",
        "ref_railway_stations",
        "ref_technologies",
        "stg_coverage_simplified",
    ]
    assert sorted(tables) == expected


def test_create_schema_is_idempotent(db_conn):
    """Vérifie que create_schema peut être appelé plusieurs fois."""
    create_schema(db_conn)
    create_schema(db_conn)

    tables = [row[0] for row in db_conn.execute("SHOW TABLES").fetchall()]
    assert len(tables) == 8


def test_seed_reference_data(db_conn):
    """Vérifie que les données de référence sont insérées."""
    create_schema(db_conn)
    seed_reference_data(db_conn)

    operators = db_conn.execute("SELECT count(*) FROM ref_operators").fetchone()[0]
    assert operators == 4

    technologies = db_conn.execute("SELECT count(*) FROM ref_technologies").fetchone()[0]
    assert technologies == 4


def test_seed_reference_data_is_idempotent(db_conn):
    """Vérifie que seed_reference_data peut être appelé plusieurs fois."""
    create_schema(db_conn)
    seed_reference_data(db_conn)
    seed_reference_data(db_conn)

    operators = db_conn.execute("SELECT count(*) FROM ref_operators").fetchone()[0]
    assert operators == 4
