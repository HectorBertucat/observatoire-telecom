"""Requêtes SQL métier réutilisables."""

import json
from typing import Any

import duckdb

from observatoire.config import settings


def get_commune_coverage(
    conn: duckdb.DuckDBPyConnection,
    commune_code: str,
    technology: str = "4G",
) -> list[dict[str, Any]]:
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
) -> list[dict[str, Any]]:
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


def get_antenna_stats(
    conn: duckdb.DuckDBPyConnection,
    operator: str | None = None,
) -> list[dict[str, Any]]:
    """Retourne les stats d'antennes par opérateur et technologie."""
    params: list[Any] = []
    where = ""
    if operator:
        where = "WHERE operator = ?"
        params.append(operator)

    result = conn.execute(
        f"""
        SELECT
            operator,
            technology,
            COUNT(*) AS site_count
        FROM raw_antenna_sites
        {where}
        GROUP BY operator, technology
        ORDER BY operator, technology
        """,
        params,
    ).fetchall()

    columns = ["operator", "technology", "site_count"]
    return [dict(zip(columns, row, strict=True)) for row in result]


def get_antenna_list(
    conn: duckdb.DuckDBPyConnection,
    operator: str | None = None,
    technology: str | None = None,
    commune_code: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Retourne une liste paginée de sites d'antennes."""
    conditions: list[str] = []
    params: list[Any] = []

    if operator:
        conditions.append("operator = ?")
        params.append(operator)
    if technology:
        conditions.append("technology = ?")
        params.append(technology)
    if commune_code:
        conditions.append("commune_code = ?")
        params.append(commune_code)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.extend([limit, offset])

    result = conn.execute(
        f"""
        SELECT id, operator, latitude, longitude, commune_code, technology
        FROM raw_antenna_sites
        {where}
        ORDER BY operator, technology, id
        LIMIT ? OFFSET ?
        """,
        params,
    ).fetchall()

    columns = ["id", "operator", "latitude", "longitude", "commune_code", "technology"]
    return [dict(zip(columns, row, strict=True)) for row in result]


def get_nearby_antennas(
    conn: duckdb.DuckDBPyConnection,
    latitude: float,
    longitude: float,
    radius_km: float = 2.0,
    technology: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Retourne les antennes proches d'un point GPS.

    Utilise une approximation haversine simplifiée (~111km/degré).
    """
    # Approximation : 1 degré ≈ 111 km
    delta = radius_km / 111.0

    conditions = [
        "latitude BETWEEN ? AND ?",
        "longitude BETWEEN ? AND ?",
    ]
    params: list[Any] = [
        latitude - delta,
        latitude + delta,
        longitude - delta,
        longitude + delta,
    ]

    if technology:
        conditions.append("technology = ?")
        params.append(technology)

    params.append(limit)
    where = " AND ".join(conditions)

    result = conn.execute(
        f"""
        SELECT
            id, operator, technology, latitude, longitude,
            commune_code, department_code,
            ROUND(111.0 * SQRT(
                POWER(latitude - {latitude}, 2) +
                POWER((longitude - {longitude}) * COS(RADIANS({latitude})), 2)
            ), 2) AS distance_km
        FROM raw_antenna_sites
        WHERE {where}
        ORDER BY distance_km
        LIMIT ?
        """,
        params,
    ).fetchall()

    columns = [
        "id", "operator", "technology", "latitude", "longitude",
        "commune_code", "department_code", "distance_km",
    ]
    return [dict(zip(columns, row, strict=True)) for row in result]


def get_coverage_geojson(operator_code: str, technology: str = "4G") -> dict[str, Any]:
    """Retourne le GeoJSON pré-simplifié depuis le fichier statique."""
    geojson_dir = settings.data_dir / "geojson"
    filename = f"coverage_{operator_code}_{technology}.geojson"
    path = geojson_dir / filename

    if not path.exists():
        return {"type": "FeatureCollection", "features": []}

    result: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return result


def get_department_antenna_stats(
    conn: duckdb.DuckDBPyConnection,
    department_code: str,
) -> list[dict[str, Any]]:
    """Retourne les stats d'antennes pour un département."""
    result = conn.execute(
        """
        SELECT
            operator, technology, COUNT(*) as site_count
        FROM raw_antenna_sites
        WHERE department_code = ?
        GROUP BY operator, technology
        ORDER BY operator, technology
        """,
        [department_code],
    ).fetchall()

    columns = ["operator", "technology", "site_count"]
    return [dict(zip(columns, row, strict=True)) for row in result]


def search_commune_antennas(
    conn: duckdb.DuckDBPyConnection,
    commune_code: str,
) -> dict[str, Any]:
    """Retourne un résumé des antennes pour une commune."""
    result = conn.execute(
        """
        SELECT
            operator, technology, COUNT(*) as cnt,
            ROUND(AVG(latitude), 5) as avg_lat,
            ROUND(AVG(longitude), 5) as avg_lon
        FROM raw_antenna_sites
        WHERE commune_code = ?
        GROUP BY operator, technology
        ORDER BY operator, technology
        """,
        [commune_code],
    ).fetchall()

    if not result:
        return {"commune_code": commune_code, "total": 0, "operators": []}

    columns = ["operator", "technology", "count", "avg_lat", "avg_lon"]
    operators = [dict(zip(columns, row, strict=True)) for row in result]
    total = sum(r[2] for r in result)
    center_lat = sum(r[3] for r in result) / len(result)
    center_lon = sum(r[4] for r in result) / len(result)

    return {
        "commune_code": commune_code,
        "total": total,
        "center": {"lat": center_lat, "lon": center_lon},
        "operators": operators,
    }


def get_table_counts(conn: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Retourne le nombre de lignes par table."""
    tables = [row[0] for row in conn.execute("SHOW TABLES").fetchall()]
    counts: dict[str, int] = {}
    for table in tables:
        count = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]  # type: ignore[index]
        counts[table] = count
    return counts
