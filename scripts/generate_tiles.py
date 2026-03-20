"""Génère un fichier PMTiles avec couvertures + antennes.

Pipeline :
  - Couverture : DuckDB (Lambert-93) → ST_Simplify(250m) → WGS84 → GeoJSON
  - Antennes : DuckDB (WGS84 points) → GeoJSON
  - Tippecanoe fusionne les deux en un seul PMTiles (z4-z14)
"""

import json
import logging
import subprocess
import sys
from pathlib import Path

from observatoire.config import settings
from observatoire.db.connection import db_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

SIMPLIFY_TOLERANCE = 1000  # mètres (Lambert-93) — bon compromis taille/détail

OPERATORS = {
    "OF": "Orange",
    "BYT": "Bouygues Telecom",
    "FREE": "Free Mobile",
    "SFR": "SFR",
}

OPERATOR_COLORS = {
    "OF": "#FF6600",
    "BYT": "#003DA5",
    "FREE": "#CD1719",
    "SFR": "#E4002B",
}


def export_coverage_geojson(technology: str = "4G") -> Path:
    """Exporte les couvertures en GeoJSON pour Tippecanoe."""
    dest = settings.data_dir / "tiles" / "coverage.geojson"
    dest.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Export couvertures (tolérance {SIMPLIFY_TOLERANCE}m)...")

    with db_session(read_only=True) as conn:
        result = conn.execute(
            """
            SELECT
                ST_AsGeoJSON(
                    ST_FlipCoordinates(
                        ST_Transform(
                            ST_Simplify(geometry, $1),
                            'EPSG:2154', 'EPSG:4326'
                        )
                    )
                ) AS geojson,
                operator_code,
                technology,
                quarter
            FROM raw_coverage
            WHERE technology = $2
            """,
            [SIMPLIFY_TOLERANCE, technology],
        ).fetchall()

    features = []
    for row in result:
        geom = json.loads(row[0])
        if not geom.get("coordinates"):
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "operator": row[1],
                    "operator_name": OPERATORS.get(row[1], row[1]),
                    "technology": row[2],
                    "quarter": row[3],
                },
            }
        )

    geojson = {"type": "FeatureCollection", "features": features}
    dest.write_text(json.dumps(geojson), encoding="utf-8")

    size_mb = dest.stat().st_size / (1024 * 1024)
    logger.info(f"Couvertures : {len(features)} features, {size_mb:.1f} MB")
    return dest


def export_antennas_geojson() -> Path:
    """Exporte les sites d'antennes en GeoJSON pour Tippecanoe."""
    dest = settings.data_dir / "tiles" / "antennas.geojson"
    dest.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Export antennes...")

    with db_session(read_only=True) as conn:
        result = conn.execute(
            """
            SELECT
                ST_AsGeoJSON(geometry) AS geojson,
                operator,
                technology,
                commune_code
            FROM raw_antenna_sites
            WHERE latitude BETWEEN 41 AND 52
              AND longitude BETWEEN -6 AND 10
            """
        ).fetchall()

    features = []
    for row in result:
        geom = json.loads(row[0])
        features.append(
            {
                "type": "Feature",
                "geometry": geom,
                "properties": {
                    "operator": row[1],
                    "operator_name": OPERATORS.get(row[1], row[1]),
                    "technology": row[2],
                    "commune": row[3],
                },
            }
        )

    geojson = {"type": "FeatureCollection", "features": features}
    dest.write_text(json.dumps(geojson), encoding="utf-8")

    size_mb = dest.stat().st_size / (1024 * 1024)
    logger.info(f"Antennes : {len(features)} features, {size_mb:.1f} MB")
    return dest


def generate_pmtiles(coverage_path: Path, antennas_path: Path) -> Path:
    """Génère un fichier PMTiles multi-couches avec Tippecanoe."""
    dest = settings.data_dir / "tiles" / "coverage.pmtiles"

    logger.info("Génération PMTiles avec Tippecanoe...")
    result = subprocess.run(
        [
            "tippecanoe",
            "-o",
            str(dest),
            "--force",
            "--name",
            "Observatoire Télécom",
            "-L",
            f"coverage:{coverage_path}",
            "--minimum-zoom=4",
            "--maximum-zoom=12",
            "--no-feature-limit",
            "--no-tile-size-limit",
            "--simplification=10",
            "--detect-shared-borders",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        logger.error(f"Tippecanoe stderr: {result.stderr}")
        raise RuntimeError(f"Tippecanoe a échoué (code {result.returncode})")

    size_mb = dest.stat().st_size / (1024 * 1024)
    logger.info(f"PMTiles couverture : {size_mb:.1f} MB")

    # Générer un PMTiles séparé pour les antennes (points)
    antennas_dest = settings.data_dir / "tiles" / "antennas.pmtiles"
    result2 = subprocess.run(
        [
            "tippecanoe",
            "-o",
            str(antennas_dest),
            "--force",
            "--name",
            "Antennes Télécom",
            "--layer",
            "antennas",
            "--minimum-zoom",
            "7",  # Points visibles à partir de z7
            "--maximum-zoom",
            "14",
            "--drop-densest-as-needed",  # Cluster aux zooms bas
            "--cluster-distance=50",  # Distance de clustering en pixels
            str(antennas_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result2.returncode != 0:
        logger.error(f"Tippecanoe antennas stderr: {result2.stderr}")
        raise RuntimeError(f"Tippecanoe antennas a échoué (code {result2.returncode})")

    size_mb2 = antennas_dest.stat().st_size / (1024 * 1024)
    logger.info(f"PMTiles antennes : {size_mb2:.1f} MB")

    return dest


def main() -> None:
    """Pipeline complète : GeoJSON → PMTiles."""
    technology = sys.argv[1] if len(sys.argv) > 1 else "4G"

    coverage_path = export_coverage_geojson(technology)
    antennas_path = export_antennas_geojson()
    generate_pmtiles(coverage_path, antennas_path)

    logger.info("Fichiers prêts dans data/tiles/")


if __name__ == "__main__":
    main()
