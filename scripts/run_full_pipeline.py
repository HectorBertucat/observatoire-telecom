"""Pipeline complète : téléchargement → extraction → chargement dans DuckDB."""

import asyncio
import logging
import sys

from observatoire.config import settings
from observatoire.db.connection import db_session
from observatoire.db.schema import create_schema, seed_reference_data
from observatoire.ingestion.downloader import (
    ARCEP_TO_DB_OPERATOR,
    OPERATOR_FILE_CODES,
    download_arcep_coverage,
)
from observatoire.ingestion.extractor import extract_7z
from observatoire.ingestion.loader import load_geopackage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def run_pipeline(
    operators: list[str] | None = None,
    technology: str = "4G",
    quarter: str | None = None,
) -> None:
    """Exécute la pipeline complète d'ingestion."""
    quarter = quarter or settings.arcep_quarter
    operators = operators or list(OPERATOR_FILE_CODES.keys())

    logger.info(f"=== Pipeline d'ingestion {quarter} ===")
    logger.info(f"Opérateurs : {operators}")
    logger.info(f"Technologie : {technology}")

    # Étape 0 : Initialiser la base
    logger.info("--- Initialisation de la base DuckDB ---")
    with db_session() as conn:
        create_schema(conn)
        seed_reference_data(conn)
    logger.info("Base initialisée.")

    # Étape 1 : Télécharger
    logger.info("--- Téléchargement des fichiers ARCEP ---")
    archives = await download_arcep_coverage(operators, technology, quarter)
    logger.info(f"{len(archives)} fichier(s) téléchargé(s).")

    # Étape 2 : Extraire
    logger.info("--- Extraction des archives ---")
    gpkg_files = []
    for archive in archives:
        gpkg = extract_7z(archive)
        gpkg_files.append(gpkg)
    logger.info(f"{len(gpkg_files)} fichier(s) extrait(s).")

    # Étape 3 : Charger dans DuckDB
    logger.info("--- Chargement dans DuckDB ---")
    total_rows = 0
    for gpkg, operator in zip(gpkg_files, operators, strict=True):
        file_code = OPERATOR_FILE_CODES[operator]
        db_code = ARCEP_TO_DB_OPERATOR[file_code]
        count = load_geopackage(gpkg, quarter, db_code, technology)
        total_rows += count
        logger.info(f"  {operator}: {count:,} géométries chargées")

    logger.info(f"=== Pipeline terminée : {total_rows:,} géométries au total ===")

    # Vérification finale
    with db_session(read_only=True) as conn:
        count = conn.execute("SELECT count(*) FROM raw_coverage").fetchone()[0]  # type: ignore[index]
        operators_loaded = conn.execute(
            "SELECT DISTINCT operator_code FROM raw_coverage"
        ).fetchall()
        logger.info(f"Base : {count:,} lignes dans raw_coverage")
        logger.info(f"Opérateurs chargés : {[r[0] for r in operators_loaded]}")


if __name__ == "__main__":
    # Par défaut, ne télécharger qu'Orange (le plus petit, ~130 MB)
    ops = sys.argv[1:] if len(sys.argv) > 1 else ["orange"]
    asyncio.run(run_pipeline(operators=ops))
