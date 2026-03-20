"""Dépendances injectées pour FastAPI."""

from collections.abc import Generator

import duckdb

from observatoire.db.connection import get_connection


def get_db() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Fournit une connexion DuckDB read-only pour les endpoints."""
    conn = get_connection(read_only=True)
    try:
        yield conn
    finally:
        conn.close()
