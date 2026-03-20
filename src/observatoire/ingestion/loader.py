"""Chargement des données dans DuckDB."""

import logging
from pathlib import Path

from observatoire.db.connection import db_session

logger = logging.getLogger(__name__)


def load_geopackage(gpkg_path: Path, quarter: str, operator: str, technology: str) -> int:
    """
    Charge un fichier GeoPackage ARCEP dans la table raw_coverage.

    DuckDB lit nativement les GeoPackage grâce à l'extension spatial + GDAL.
    ST_Read() parse le format géospatial et retourne une table avec une colonne geometry.
    """
    with db_session() as conn:
        conn.execute(
            """
            INSERT INTO raw_coverage
                (quarter, operator_code, technology, usage, geometry, source_file)
            SELECT
                $1 AS quarter,
                $2 AS operator_code,
                $3 AS technology,
                'data' AS usage,
                geom AS geometry,
                $4 AS source_file
            FROM ST_Read($5)
            """,
            [quarter, operator, technology, gpkg_path.name, str(gpkg_path)],
        )

        count: int = conn.execute(
            "SELECT count(*) FROM raw_coverage WHERE source_file = ?",
            [gpkg_path.name],
        ).fetchone()[0]  # type: ignore[index]

        logger.info(f"Chargé {count:,} géométries depuis {gpkg_path.name}")
        return count
