"""Requêtes SQL métier réutilisables."""

import json

import duckdb

from observatoire.config import settings


def get_commune_coverage(
    conn: duckdb.DuckDBPyConnection,
    commune_code: str,
    technology: str = "4G",
) -> list[dict]:
    """Retourne la couverture d'une commune par opérateur."""
    result = conn.execute(
        """
        SELECT
            commune_code,
            commune_name,
            operator_code AS operator,
            technology,
            coverage_pct,
            antenna_count,
            total_population AS population
        FROM mart_coverage_by_commune
        WHERE commune_code = ?
          AND technology = ?
        ORDER BY coverage_pct DESC
        """,
        [commune_code, technology],
    ).fetchall()

    columns = [
        "commune_code",
        "commune_name",
        "operator",
        "technology",
        "coverage_pct",
        "antenna_count",
        "population",
    ]
    return [dict(zip(columns, row, strict=True)) for row in result]


def get_raw_coverage_stats(
    conn: duckdb.DuckDBPyConnection,
    technology: str = "4G",
) -> list[dict]:
    """Retourne les stats de couverture par opérateur depuis raw_coverage."""
    result = conn.execute(
        """
        SELECT
            rc.operator_code AS operator,
            ro.name AS operator_name,
            rc.technology,
            COUNT(*) AS geometry_count,
            rc.quarter
        FROM raw_coverage rc
        LEFT JOIN ref_operators ro ON rc.operator_code = ro.code
        WHERE rc.technology = ?
        GROUP BY rc.operator_code, ro.name, rc.technology, rc.quarter
        ORDER BY rc.operator_code
        """,
        [technology],
    ).fetchall()

    columns = ["operator", "operator_name", "technology", "geometry_count", "quarter"]
    return [dict(zip(columns, row, strict=True)) for row in result]


def get_coverage_geojson(operator_code: str, technology: str = "4G") -> dict:
    """Retourne le GeoJSON pré-simplifié depuis le fichier statique."""
    geojson_dir = settings.data_dir / "geojson"
    filename = f"coverage_{operator_code}_{technology}.geojson"
    path = geojson_dir / filename

    if not path.exists():
        return {"type": "FeatureCollection", "features": []}

    return json.loads(path.read_text(encoding="utf-8"))


def list_available_geojson() -> list[dict]:
    """Liste les fichiers GeoJSON disponibles avec leur taille."""
    geojson_dir = settings.data_dir / "geojson"
    if not geojson_dir.exists():
        return []

    files = []
    for path in sorted(geojson_dir.glob("*.geojson")):
        files.append(
            {
                "filename": path.name,
                "size_kb": round(path.stat().st_size / 1024),
            }
        )
    return files


def get_table_counts(conn: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Retourne le nombre de lignes par table."""
    tables = [row[0] for row in conn.execute("SHOW TABLES").fetchall()]
    counts: dict[str, int] = {}
    for table in tables:
        count = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]  # type: ignore[index]
        counts[table] = count
    return counts
