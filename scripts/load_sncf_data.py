"""Pipeline de chargement des donnees SNCF (lignes RFN + gares).

Usage :
    uv run python scripts/load_sncf_data.py
"""

import asyncio
import logging

from observatoire.db.connection import db_session
from observatoire.db.schema import create_schema, seed_reference_data
from observatoire.ingestion.sncf_downloader import (
    download_sncf_lines,
    download_sncf_stations,
)
from observatoire.ingestion.sncf_loader import load_railway_lines, load_railway_stations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def run_pipeline() -> None:
    """Execute le pipeline SNCF complet."""
    # Etape 0 : schema
    logger.info("=== Etape 0 : Schema ===")
    with db_session() as conn:
        create_schema(conn)
        seed_reference_data(conn)

    # Etape 1 : telechargement
    logger.info("=== Etape 1 : Telechargement ===")
    lines_path = await download_sncf_lines()
    stations_path = await download_sncf_stations()

    # Etape 2 : chargement (gares d'abord pour construire les noms de lignes)
    logger.info("=== Etape 2 : Chargement ===")
    stations_count = load_railway_stations(stations_path)
    lines_count = load_railway_lines(lines_path)

    # Etape 3 : couverture simplifiee (si des donnees de couverture existent)
    logger.info("=== Etape 3 : Couverture simplifiee ===")
    with db_session() as conn:
        raw_count = conn.execute("SELECT COUNT(*) FROM raw_coverage").fetchone()[0]  # type: ignore[index]
        if raw_count > 0:
            from observatoire.db.queries import populate_simplified_coverage

            simplified = populate_simplified_coverage(conn)
            logger.info(f"  {simplified:,} couvertures simplifiees")
        else:
            logger.info("  (pas de donnees de couverture en base)")

    # Verification
    logger.info("=== Resultat ===")
    logger.info(f"  Lignes ferroviaires : {lines_count:,}")
    logger.info(f"  Gares voyageurs     : {stations_count:,}")

    with db_session(read_only=True) as conn:
        total_lines = conn.execute("SELECT COUNT(*) FROM ref_railway_lines").fetchone()[0]  # type: ignore[index]
        total_stations = conn.execute("SELECT COUNT(*) FROM ref_railway_stations").fetchone()[0]  # type: ignore[index]
        total_length = conn.execute(
            "SELECT ROUND(SUM(length_km), 0) FROM ref_railway_lines"
        ).fetchone()[0]  # type: ignore[index]
        logger.info(f"  Total en base : {total_lines} lignes ({total_length} km), {total_stations} gares")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
