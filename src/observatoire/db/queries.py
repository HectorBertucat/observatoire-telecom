"""Requêtes SQL métier réutilisables."""

import json

import duckdb


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


def get_coverage_geojson(
    conn: duckdb.DuckDBPyConnection,
    operator_code: str,
    technology: str = "4G",
    limit: int = 10,
) -> dict:
    """Retourne les enveloppes de couverture en GeoJSON.

    Les géométries ARCEP sont trop lourdes (~200k points chacune) pour
    être servies en GeoJSON. On retourne les enveloppes (bounding boxes)
    qui sont instantanées à calculer.
    """
    result = conn.execute(
        """
        SELECT
            ST_AsGeoJSON(
                ST_FlipCoordinates(
                    ST_Transform(ST_Envelope(geometry), 'EPSG:2154', 'EPSG:4326')
                )
            ) AS geojson,
            operator_code,
            technology,
            quarter,
            ST_NPoints(geometry) AS npoints
        FROM raw_coverage
        WHERE operator_code = $1
          AND technology = $2
        LIMIT $3
        """,
        [operator_code, technology, limit],
    ).fetchall()

    features = []
    for row in result:
        features.append(
            {
                "type": "Feature",
                "geometry": json.loads(row[0]),
                "properties": {
                    "operator": row[1],
                    "technology": row[2],
                    "quarter": row[3],
                    "detail_points": row[4],
                },
            }
        )

    return {"type": "FeatureCollection", "features": features}


def get_table_counts(conn: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Retourne le nombre de lignes par table."""
    tables = [row[0] for row in conn.execute("SHOW TABLES").fetchall()]
    counts: dict[str, int] = {}
    for table in tables:
        count = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]  # type: ignore[index]
        counts[table] = count
    return counts
