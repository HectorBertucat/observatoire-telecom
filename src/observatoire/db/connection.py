"""Gestion de la connexion DuckDB."""

import logging
from collections.abc import Generator
from contextlib import contextmanager

import duckdb

from observatoire.config import settings

logger = logging.getLogger(__name__)


def get_connection(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Crée une connexion DuckDB avec les extensions chargées."""
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(settings.db_path), read_only=read_only)

    # Charger l'extension spatiale (indispensable pour les GeoPackage)
    conn.install_extension("spatial")
    conn.load_extension("spatial")

    logger.debug(f"Connexion DuckDB ouverte (read_only={read_only})")
    return conn


@contextmanager
def db_session(read_only: bool = False) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Context manager pour une session DuckDB."""
    conn = get_connection(read_only=read_only)
    try:
        yield conn
    finally:
        conn.close()
