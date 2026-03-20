"""Pré-calcul des géométries simplifiées pour l'affichage web."""

import json
import logging
from pathlib import Path

import duckdb

from observatoire.config import settings

logger = logging.getLogger(__name__)

# Tolérance de simplification en mètres (données en Lambert-93 / EPSG:2154)
SIMPLIFY_TOLERANCE = 5000  # 5 km — bon compromis taille/fidélité


def export_operator_geojson(
    conn: duckdb.DuckDBPyConnection,
    operator_code: str,
    technology: str = "4G",
    dest_dir: Path | None = None,
) -> Path:
    """Exporte les géométries simplifiées d'un opérateur en GeoJSON statique.

    Pipeline : Lambert-93 → Simplify(5km) → WGS84 → GeoJSON
    Résultat : ~60-120 points par géométrie au lieu de ~200k.
    """
    dest_dir = dest_dir or settings.data_dir / "geojson"
    dest_dir.mkdir(parents=True, exist_ok=True)

    result = conn.execute(
        """
        SELECT
            ST_AsGeoJSON(
                ST_FlipCoordinates(
                    ST_Transform(
                        ST_Simplify(geometry, $3),
                        'EPSG:2154', 'EPSG:4326'
                    )
                )
            ) AS geojson,
            operator_code,
            technology,
            quarter
        FROM raw_coverage
        WHERE operator_code = $1
          AND technology = $2
        """,
        [operator_code, technology, SIMPLIFY_TOLERANCE],
    ).fetchall()

    features = []
    for row in result:
        geom = json.loads(row[0])
        # Filtrer les géométries vides après simplification
        if geom.get("coordinates"):
            features.append(
                {
                    "type": "Feature",
                    "geometry": geom,
                    "properties": {
                        "operator": row[1],
                        "technology": row[2],
                        "quarter": row[3],
                    },
                }
            )

    geojson = {"type": "FeatureCollection", "features": features}

    filename = f"coverage_{operator_code}_{technology}.geojson"
    dest = dest_dir / filename
    dest.write_text(json.dumps(geojson), encoding="utf-8")

    size_kb = dest.stat().st_size / 1024
    logger.info(f"{filename}: {len(features)} features, {size_kb:.0f} KB")
    return dest


def export_all_geojson(conn: duckdb.DuckDBPyConnection, technology: str = "4G") -> list[Path]:
    """Exporte les GeoJSON simplifiés pour tous les opérateurs."""
    operators = [r[0] for r in conn.execute("SELECT code FROM ref_operators").fetchall()]
    paths = []
    for op in operators:
        path = export_operator_geojson(conn, op, technology)
        paths.append(path)
    return paths
