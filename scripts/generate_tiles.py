"""Génère un fichier PMTiles à partir des données de couverture ARCEP.

Pipeline : DuckDB (Lambert-93) → GeoJSON (WGS84, simplifié 500m) → Tippecanoe → PMTiles
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

# Tolérance en mètres (Lambert-93) — 500m pour garder du détail
SIMPLIFY_TOLERANCE = 500

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


def export_geojson_for_tiles(technology: str = "4G") -> Path:
    """Exporte toutes les couvertures en un seul GeoJSON pour Tippecanoe."""
    dest = settings.data_dir / "tiles" / "all_coverage.geojson"
    dest.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Export GeoJSON (tolérance {SIMPLIFY_TOLERANCE}m)...")

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
                    "color": OPERATOR_COLORS.get(row[1], "#999"),
                },
            }
        )

    geojson = {"type": "FeatureCollection", "features": features}
    dest.write_text(json.dumps(geojson), encoding="utf-8")

    size_mb = dest.stat().st_size / (1024 * 1024)
    logger.info(f"GeoJSON exporté : {len(features)} features, {size_mb:.1f} MB")
    return dest


def generate_pmtiles(geojson_path: Path) -> Path:
    """Génère un fichier PMTiles avec Tippecanoe."""
    dest = settings.data_dir / "tiles" / "coverage.pmtiles"

    logger.info("Génération PMTiles avec Tippecanoe...")
    result = subprocess.run(
        [
            "tippecanoe",
            "-o", str(dest),
            "--force",                    # Écraser si existant
            "--name", "Observatoire Télécom",
            "--layer", "coverage",        # Nom de la couche
            "--minimum-zoom", "4",        # Zoom min (France entière)
            "--maximum-zoom", "12",       # Zoom max (quartier)
            "--simplification", "10",     # Simplification supplémentaire
            "--detect-shared-borders",    # Évite les artefacts aux bordures
            "--coalesce-densest-as-needed",  # Fusionne si trop dense
            "--extend-zooms-if-still-dropping",  # Garde le détail si nécessaire
            str(geojson_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        logger.error(f"Tippecanoe stderr: {result.stderr}")
        raise RuntimeError(f"Tippecanoe a échoué (code {result.returncode})")

    size_mb = dest.stat().st_size / (1024 * 1024)
    logger.info(f"PMTiles généré : {size_mb:.1f} MB")
    return dest


def main() -> None:
    """Pipeline complète : GeoJSON → PMTiles."""
    technology = sys.argv[1] if len(sys.argv) > 1 else "4G"

    geojson_path = export_geojson_for_tiles(technology)
    pmtiles_path = generate_pmtiles(geojson_path)

    logger.info(f"Fichier prêt : {pmtiles_path}")
    logger.info("Servir via FastAPI StaticFiles ou directement depuis data/tiles/")


if __name__ == "__main__":
    main()
