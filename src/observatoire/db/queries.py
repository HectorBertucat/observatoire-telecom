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


def get_railway_lines(
    conn: duckdb.DuckDBPyConnection,
    search: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Retourne la liste des lignes ferroviaires (sans geometrie)."""
    conditions: list[str] = []
    params: list[Any] = []

    if search:
        conditions.append("(LOWER(line_name) LIKE ? OR line_id LIKE ?)")
        pattern = f"%{search.lower()}%"
        params.extend([pattern, f"%{search}%"])

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)

    result = conn.execute(
        f"""
        SELECT line_id, line_name, ROUND(length_km, 1) AS length_km
        FROM ref_railway_lines
        {where}
        ORDER BY line_name
        LIMIT ?
        """,
        params,
    ).fetchall()

    columns = ["line_id", "line_name", "length_km"]
    return [dict(zip(columns, row, strict=True)) for row in result]


def get_railway_stations(
    conn: duckdb.DuckDBPyConnection,
    search: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Retourne la liste des gares (pour autocomplete).

    Deduplication par nom de gare : une gare peut apparaitre sur
    plusieurs lignes, on retourne une seule entree par nom avec
    la liste des codes ligne.
    """
    conditions: list[str] = []
    params: list[Any] = []

    if search:
        conditions.append("LOWER(station_name) LIKE ?")
        params.append(f"%{search.lower()}%")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)

    result = conn.execute(
        f"""
        SELECT
            MIN(station_id) AS station_id,
            station_name,
            STRING_AGG(DISTINCT line_code, ',') AS line_codes,
            MIN(commune) AS commune,
            MIN(department) AS department,
            ROUND(AVG(latitude), 6) AS latitude,
            ROUND(AVG(longitude), 6) AS longitude
        FROM ref_railway_stations
        {where}
        GROUP BY station_name
        ORDER BY station_name
        LIMIT ?
        """,
        params,
    ).fetchall()

    columns = [
        "station_id",
        "station_name",
        "line_codes",
        "commune",
        "department",
        "latitude",
        "longitude",
    ]
    return [dict(zip(columns, row, strict=True)) for row in result]


def get_route_coverage(
    conn: duckdb.DuckDBPyConnection,
    line_id: str,
    technology: str = "4G",
    buffer_km: float = 2.0,
) -> list[dict[str, Any]]:
    """Calcule la couverture reseau le long d'une ligne ferroviaire.

    Algorithme :
    1. Recuperer la geometrie de la ligne (Lambert-93)
    2. Creer un buffer de N km autour du trace
    3. Intersecter avec raw_coverage pour chaque operateur
    4. Calculer le % de longueur couverte
    """
    buffer_m = buffer_km * 1000

    # Utilise stg_coverage_simplified (pre-calcule) pour des requetes
    # rapides. Filtre par bounding box pre-stocke, puis intersection
    # avec les geometries simplifiees.
    result = conn.execute(
        """
        WITH line AS (
            SELECT geometry, length_km
            FROM ref_railway_lines
            WHERE line_id = ?
            LIMIT 1
        ),
        candidates AS (
            SELECT sc.operator_code,
                   sc.geometry,
                   ro.name AS operator_name
            FROM stg_coverage_simplified sc
            LEFT JOIN ref_operators ro ON sc.operator_code = ro.code,
                 line l
            WHERE sc.technology = ?
              AND sc.bbox_xmax >= ST_XMin(l.geometry) - ?
              AND sc.bbox_xmin <= ST_XMax(l.geometry) + ?
              AND sc.bbox_ymax >= ST_YMin(l.geometry) - ?
              AND sc.bbox_ymin <= ST_YMax(l.geometry) + ?
        ),
        coverage_intersection AS (
            SELECT
                c.operator_code,
                c.operator_name,
                l.length_km AS total_length_km,
                ST_Length(ST_Intersection(l.geometry, c.geometry))
                    / 1000.0 AS covered_length_km
            FROM line l
            CROSS JOIN candidates c
            WHERE ST_Intersects(l.geometry, c.geometry)
        )
        SELECT
            operator_code,
            operator_name,
            MAX(total_length_km) AS total_length_km,
            ROUND(
                LEAST(SUM(covered_length_km), MAX(total_length_km)), 1
            ) AS covered_length_km,
            ROUND(
                LEAST(
                    SUM(covered_length_km)
                    / NULLIF(MAX(total_length_km), 0) * 100,
                    100
                ),
                1
            ) AS coverage_pct
        FROM coverage_intersection
        GROUP BY operator_code, operator_name
        ORDER BY coverage_pct DESC
        """,
        [line_id, technology, buffer_m, buffer_m, buffer_m, buffer_m],
    ).fetchall()

    columns = [
        "operator",
        "operator_name",
        "total_length_km",
        "covered_length_km",
        "coverage_pct",
    ]
    return [dict(zip(columns, row, strict=True)) for row in result]


def get_route_geojson(
    conn: duckdb.DuckDBPyConnection,
    line_id: str,
) -> dict[str, Any]:
    """Retourne le GeoJSON d'une ligne ferroviaire (WGS84)."""
    result = conn.execute(
        """
        SELECT
            ST_AsGeoJSON(
                ST_FlipCoordinates(
                    ST_Transform(geometry, 'EPSG:2154', 'EPSG:4326')
                )
            ) AS geojson,
            line_id,
            line_name,
            ROUND(length_km, 1) AS length_km
        FROM ref_railway_lines
        WHERE line_id = ?
        LIMIT 1
        """,
        [line_id],
    ).fetchone()

    if not result:
        return {"type": "FeatureCollection", "features": []}

    geom = json.loads(result[0])
    feature: dict[str, Any] = {
        "type": "Feature",
        "geometry": geom,
        "properties": {
            "line_id": result[1],
            "line_name": result[2],
            "length_km": result[3],
        },
    }
    return {"type": "FeatureCollection", "features": [feature]}


def find_transfer_options(
    conn: duckdb.DuckDBPyConnection,
    dep_line_ids: list[str],
    arr_line_ids: list[str],
    dep_lat: float,
    dep_lon: float,
    arr_lat: float,
    arr_lon: float,
) -> list[dict[str, Any]]:
    """Trouve les correspondances entre deux groupes de lignes.

    Utilise la proximite geometrique (ST_DWithin 500m) pour trouver
    une ligne-pont, puis identifie la gare de correspondance la plus
    proche du point de jonction entre la ligne depart et la ligne-pont.
    Deduplication par gare de correspondance (une seule option par ville).
    """
    if not dep_line_ids or not arr_line_ids:
        return []

    dep_ph = ", ".join(["?"] * len(dep_line_ids))
    arr_ph = ", ".join(["?"] * len(arr_line_ids))

    result = conn.execute(
        f"""
        WITH bridge AS (
            SELECT DISTINCT l_bridge.line_id, l_bridge.line_name,
                   l_bridge.length_km, l_bridge.geometry,
                   l_dep.geometry AS dep_geometry
            FROM ref_railway_lines l_dep
            JOIN ref_railway_lines l_bridge
                ON l_dep.line_id != l_bridge.line_id
                AND ST_DWithin(l_dep.geometry, l_bridge.geometry, 500)
            JOIN ref_railway_lines l_arr
                ON l_bridge.line_id != l_arr.line_id
                AND ST_DWithin(l_bridge.geometry, l_arr.geometry, 500)
            WHERE l_dep.line_id IN ({dep_ph})
              AND l_arr.line_id IN ({arr_ph})
              AND l_bridge.line_id NOT IN ({dep_ph})
              AND l_bridge.line_id NOT IN ({arr_ph})
        ),
        bridge_with_station AS (
            SELECT
                b.line_id,
                b.line_name,
                ROUND(b.length_km, 1) AS length_km,
                -- Trouver la gare la plus proche du point de contact
                -- entre la ligne depart et la ligne-pont
                (SELECT s.station_name
                 FROM ref_railway_stations s
                 WHERE s.line_code = b.line_id
                    OR s.line_code IN ({dep_ph})
                 ORDER BY ST_Distance(
                     ST_Transform(
                         ST_FlipCoordinates(ST_Point(s.longitude, s.latitude)),
                         'EPSG:4326', 'EPSG:2154'
                     ),
                     ST_ClosestPoint(b.dep_geometry, b.geometry)
                 )
                 LIMIT 1
                ) AS transfer_station
            FROM bridge b
        )
        SELECT line_id, line_name, length_km, transfer_station
        FROM bridge_with_station
        WHERE transfer_station IS NOT NULL
        GROUP BY transfer_station, line_id, line_name, length_km
        ORDER BY length_km DESC
        """,
        [
            *dep_line_ids,
            *arr_line_ids,
            *dep_line_ids,
            *arr_line_ids,
            *dep_line_ids,
        ],
    ).fetchall()

    # Deduplication par gare de correspondance
    # Exclure les gares de depart/arrivee (pas une vraie correspondance)
    dep_station = conn.execute(
        "SELECT station_name FROM ref_railway_stations "
        "ORDER BY (latitude - ?) * (latitude - ?) "
        "+ (longitude - ?) * (longitude - ?) LIMIT 1",
        [dep_lat, dep_lat, dep_lon, dep_lon],
    ).fetchone()
    arr_station = conn.execute(
        "SELECT station_name FROM ref_railway_stations "
        "ORDER BY (latitude - ?) * (latitude - ?) "
        "+ (longitude - ?) * (longitude - ?) LIMIT 1",
        [arr_lat, arr_lat, arr_lon, arr_lon],
    ).fetchone()
    exclude = {dep_station[0] if dep_station else "", arr_station[0] if arr_station else ""}

    seen_stations: set[str] = set()
    deduped: list[dict[str, Any]] = []
    columns = ["line_id", "line_name", "length_km", "transfer_station"]
    for row in result:
        d = dict(zip(columns, row, strict=True))
        station = d["transfer_station"]
        if station not in seen_stations and station not in exclude:
            seen_stations.add(station)
            deduped.append(d)
    return deduped[:5]


def get_route_segment_geojson(
    conn: duckdb.DuckDBPyConnection,
    line_id: str,
    from_lat: float,
    from_lon: float,
    to_lat: float,
    to_lon: float,
) -> dict[str, Any]:
    """Retourne le GeoJSON d'un segment de ligne entre deux points.

    Utilise ST_LineLocatePoint pour trouver les fractions sur la ligne,
    puis extrait les coordonnees entre ces deux points.
    """
    result = conn.execute(
        """
        SELECT
            ST_AsGeoJSON(
                ST_FlipCoordinates(
                    ST_Transform(geometry, 'EPSG:2154', 'EPSG:4326')
                )
            ) AS geojson,
            ST_LineLocatePoint(
                geometry,
                ST_Transform(
                    ST_FlipCoordinates(ST_Point(?, ?)),
                    'EPSG:4326', 'EPSG:2154'
                )
            ) AS frac_from,
            ST_LineLocatePoint(
                geometry,
                ST_Transform(
                    ST_FlipCoordinates(ST_Point(?, ?)),
                    'EPSG:4326', 'EPSG:2154'
                )
            ) AS frac_to,
            line_id,
            line_name,
            ROUND(length_km, 1) AS length_km
        FROM ref_railway_lines
        WHERE line_id = ?
        LIMIT 1
        """,
        [from_lon, from_lat, to_lon, to_lat, line_id],
    ).fetchone()

    if not result:
        return {"type": "FeatureCollection", "features": []}

    full_geom = json.loads(result[0])
    frac_from = min(result[1], result[2])
    frac_to = max(result[1], result[2])

    # Extraire le sous-segment des coordonnees
    coords = full_geom.get("coordinates", [])
    if full_geom.get("type") == "MultiLineString":
        # Aplatir en une seule liste de coords
        coords = [c for part in coords for c in part]

    if len(coords) > 1:
        start_idx = max(0, int(frac_from * (len(coords) - 1)))
        end_idx = min(len(coords) - 1, int(frac_to * (len(coords) - 1)) + 1)
        if end_idx <= start_idx:
            end_idx = start_idx + 1
        segment_coords = coords[start_idx:end_idx]
    else:
        segment_coords = coords

    segment_km = round(result[5] * (frac_to - frac_from), 1)

    feature: dict[str, Any] = {
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": segment_coords},
        "properties": {
            "line_id": result[3],
            "line_name": result[4],
            "length_km": segment_km,
            "type": "route",
        },
    }
    return {"type": "FeatureCollection", "features": [feature]}


def populate_simplified_coverage(conn: duckdb.DuckDBPyConnection) -> int:
    """Pre-calcule les couvertures simplifiees pour les analyses spatiales.

    Simplifie les geometries (tolerance 5km en Lambert-93) et stocke
    les bounding boxes pour permettre un filtrage rapide.
    """
    conn.execute("DELETE FROM stg_coverage_simplified")
    conn.execute("""
        INSERT INTO stg_coverage_simplified
            (operator_code, technology, geometry,
             bbox_xmin, bbox_ymin, bbox_xmax, bbox_ymax)
        SELECT
            operator_code,
            technology,
            ST_Simplify(geometry, 5000),
            ST_XMin(geometry),
            ST_YMin(geometry),
            ST_XMax(geometry),
            ST_YMax(geometry)
        FROM raw_coverage
    """)
    count: int = conn.execute("SELECT COUNT(*) FROM stg_coverage_simplified").fetchone()[0]  # type: ignore[index]
    return count


def get_table_counts(conn: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Retourne le nombre de lignes par table."""
    tables = [row[0] for row in conn.execute("SHOW TABLES").fetchall()]
    counts: dict[str, int] = {}
    for table in tables:
        count = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]  # type: ignore[index]
        counts[table] = count
    return counts
