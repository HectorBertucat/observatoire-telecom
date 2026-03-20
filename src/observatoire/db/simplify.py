"""Pré-calcul des géométries simplifiées pour l'affichage."""

import logging

import duckdb

logger = logging.getLogger(__name__)


def create_simplified_coverage(conn: duckdb.DuckDBPyConnection) -> int:
    """Crée une table de couverture avec géométries simplifiées pour la carte.

    Les géométries ARCEP brutes ont ~200k points chacune.
    On les simplifie agressivement (tolérance 0.01°, ~1km) pour le rendu web.
    """
    logger.info("Création de stg_coverage_simplified...")

    conn.execute("DROP TABLE IF EXISTS stg_coverage_simplified")
    conn.execute("""
        CREATE TABLE stg_coverage_simplified AS
        SELECT
            row_number() OVER () AS id,
            operator_code,
            technology,
            quarter,
            ST_Simplify(geometry, 0.1) AS geometry,
            ST_NPoints(ST_Simplify(geometry, 0.1)) AS npoints
        FROM raw_coverage
    """)

    count: int = conn.execute(
        "SELECT count(*) FROM stg_coverage_simplified"
    ).fetchone()[0]  # type: ignore[index]

    total_points: int = conn.execute(
        "SELECT SUM(npoints) FROM stg_coverage_simplified"
    ).fetchone()[0]  # type: ignore[index]

    logger.info(
        f"stg_coverage_simplified: {count} géométries, "
        f"{total_points:,} points total (vs ~230M bruts)"
    )
    return count
