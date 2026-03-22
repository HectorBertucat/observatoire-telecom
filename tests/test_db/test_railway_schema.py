"""Tests pour les tables SNCF (ref_railway_lines, ref_railway_stations)."""

from observatoire.db.schema import create_schema


def test_create_railway_tables(db_conn):
    """Verifie que les tables ferroviaires sont creees."""
    create_schema(db_conn)

    tables = [row[0] for row in db_conn.execute("SHOW TABLES").fetchall()]
    assert "ref_railway_lines" in tables
    assert "ref_railway_stations" in tables


def test_railway_schema_idempotent(db_conn):
    """Verifie que create_schema est idempotent pour les tables SNCF."""
    create_schema(db_conn)
    create_schema(db_conn)

    count = db_conn.execute("SELECT COUNT(*) FROM ref_railway_lines").fetchone()[0]
    assert count == 0


def test_railway_lines_columns(db_conn):
    """Verifie les colonnes de ref_railway_lines."""
    create_schema(db_conn)

    columns = db_conn.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'ref_railway_lines' ORDER BY ordinal_position"
    ).fetchall()
    col_names = [c[0] for c in columns]

    assert "line_id" in col_names
    assert "line_name" in col_names
    assert "geometry" in col_names
    assert "length_km" in col_names


def test_railway_stations_columns(db_conn):
    """Verifie les colonnes de ref_railway_stations."""
    create_schema(db_conn)

    columns = db_conn.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'ref_railway_stations' ORDER BY ordinal_position"
    ).fetchall()
    col_names = [c[0] for c in columns]

    assert "station_id" in col_names
    assert "station_name" in col_names
    assert "line_code" in col_names
    assert "latitude" in col_names
    assert "longitude" in col_names
