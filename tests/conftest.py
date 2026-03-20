"""Fixtures pytest partagées."""

import duckdb
import pytest


@pytest.fixture
def db_conn(tmp_path):
    """Connexion DuckDB en mémoire pour les tests."""
    db_path = tmp_path / "test.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.install_extension("spatial")
    conn.load_extension("spatial")
    yield conn
    conn.close()
