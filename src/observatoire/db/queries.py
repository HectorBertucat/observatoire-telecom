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
        "id",
        "operator",
        "technology",
        "latitude",
        "longitude",
        "commune_code",
        "department_code",
        "distance_km",
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


DEPARTMENT_NAMES: dict[str, str] = {
    "01": "Ain",
    "02": "Aisne",
    "03": "Allier",
    "04": "Alpes-de-Haute-Provence",
    "05": "Hautes-Alpes",
    "06": "Alpes-Maritimes",
    "07": "Ardèche",
    "08": "Ardennes",
    "09": "Ariège",
    "10": "Aube",
    "11": "Aude",
    "12": "Aveyron",
    "13": "Bouches-du-Rhône",
    "14": "Calvados",
    "15": "Cantal",
    "16": "Charente",
    "17": "Charente-Maritime",
    "18": "Cher",
    "19": "Corrèze",
    "21": "Côte-d'Or",
    "22": "Côtes-d'Armor",
    "23": "Creuse",
    "24": "Dordogne",
    "25": "Doubs",
    "26": "Drôme",
    "27": "Eure",
    "28": "Eure-et-Loir",
    "29": "Finistère",
    "2A": "Corse-du-Sud",
    "2B": "Haute-Corse",
    "30": "Gard",
    "31": "Haute-Garonne",
    "32": "Gers",
    "33": "Gironde",
    "34": "Hérault",
    "35": "Ille-et-Vilaine",
    "36": "Indre",
    "37": "Indre-et-Loire",
    "38": "Isère",
    "39": "Jura",
    "40": "Landes",
    "41": "Loir-et-Cher",
    "42": "Loire",
    "43": "Haute-Loire",
    "44": "Loire-Atlantique",
    "45": "Loiret",
    "46": "Lot",
    "47": "Lot-et-Garonne",
    "48": "Lozère",
    "49": "Maine-et-Loire",
    "50": "Manche",
    "51": "Marne",
    "52": "Haute-Marne",
    "53": "Mayenne",
    "54": "Meurthe-et-Moselle",
    "55": "Meuse",
    "56": "Morbihan",
    "57": "Moselle",
    "58": "Nièvre",
    "59": "Nord",
    "60": "Oise",
    "61": "Orne",
    "62": "Pas-de-Calais",
    "63": "Puy-de-Dôme",
    "64": "Pyrénées-Atlantiques",
    "65": "Hautes-Pyrénées",
    "66": "Pyrénées-Orientales",
    "67": "Bas-Rhin",
    "68": "Haut-Rhin",
    "69": "Rhône",
    "70": "Haute-Saône",
    "71": "Saône-et-Loire",
    "72": "Sarthe",
    "73": "Savoie",
    "74": "Haute-Savoie",
    "75": "Paris",
    "76": "Seine-Maritime",
    "77": "Seine-et-Marne",
    "78": "Yvelines",
    "79": "Deux-Sèvres",
    "80": "Somme",
    "81": "Tarn",
    "82": "Tarn-et-Garonne",
    "83": "Var",
    "84": "Vaucluse",
    "85": "Vendée",
    "86": "Vienne",
    "87": "Haute-Vienne",
    "88": "Vosges",
    "89": "Yonne",
    "90": "Territoire de Belfort",
    "91": "Essonne",
    "92": "Hauts-de-Seine",
    "93": "Seine-Saint-Denis",
    "94": "Val-de-Marne",
    "95": "Val-d'Oise",
    "971": "Guadeloupe",
    "972": "Martinique",
    "973": "Guyane",
    "974": "La Réunion",
    "976": "Mayotte",
}


def list_departments(conn: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    """Retourne la liste des départements avec nombre d'antennes."""
    result = conn.execute("""
        SELECT department_code, COUNT(*) as antenna_count
        FROM raw_antenna_sites
        WHERE department_code IS NOT NULL
        GROUP BY department_code
        ORDER BY department_code
    """).fetchall()

    return [
        {
            "code": row[0],
            "name": DEPARTMENT_NAMES.get(row[0], row[0]),
            "antenna_count": row[1],
        }
        for row in result
    ]


def get_top_communes(
    conn: duckdb.DuckDBPyConnection,
    department_code: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Retourne les communes avec le plus d'antennes."""
    params: list[Any] = []
    where = ""
    if department_code:
        where = "WHERE department_code = ?"
        params.append(department_code)
    params.append(limit)

    result = conn.execute(
        f"""
        SELECT commune_code, commune_name, department_code,
               SUM(antenna_count) as total
        FROM mart_coverage_by_commune
        {where}
        GROUP BY commune_code, commune_name, department_code
        ORDER BY total DESC
        LIMIT ?
        """,
        params,
    ).fetchall()

    columns = ["commune_code", "commune_name", "department_code", "total"]
    return [dict(zip(columns, row, strict=True)) for row in result]


def get_table_counts(conn: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Retourne le nombre de lignes par table."""
    tables = [row[0] for row in conn.execute("SHOW TABLES").fetchall()]
    counts: dict[str, int] = {}
    for table in tables:
        count = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]  # type: ignore[index]
        counts[table] = count
    return counts
