"""Chargement des donnees SNCF dans DuckDB."""

import json
import logging
from pathlib import Path

import duckdb

from observatoire.db.connection import db_session

logger = logging.getLogger(__name__)


def load_railway_lines(geojson_path: Path) -> int:
    """Charge les lignes ferroviaires RFN dans ref_railway_lines.

    Les geometries sont transformees en Lambert-93 (EPSG:2154) pour
    etre coherentes avec raw_coverage et permettre les calculs de
    buffer en metres.

    Le champ `libelle` du GeoJSON SNCF contient le statut de la ligne
    (Exploitee, Neutralisee...) et non son nom. On ne garde que les
    lignes exploitees.
    """
    with db_session() as conn:
        data = json.loads(geojson_path.read_text(encoding="utf-8"))
        features = data.get("features", [])

        if not features:
            logger.warning("Aucune feature dans le fichier GeoJSON lignes")
            return 0

        conn.execute("DELETE FROM ref_railway_lines")

        inserted = 0
        for feat in features:
            props = feat.get("properties", {})
            geom = feat.get("geometry")
            if not geom:
                continue

            # Ne garder que les lignes exploitees
            statut = str(props.get("libelle", ""))
            if statut != "Exploitée":
                continue

            line_id = str(props.get("code_ligne", ""))
            # Le nom sera construit a posteriori depuis les gares
            line_name = ""

            geom_json = json.dumps(geom)

            # GeoJSON = (lon, lat) mais EPSG:4326 attend (lat, lon)
            # → FlipCoordinates AVANT ST_Transform
            conn.execute(
                """
                INSERT INTO ref_railway_lines (line_id, line_name, geometry, length_km)
                VALUES (
                    $1, $2,
                    ST_Transform(
                        ST_FlipCoordinates(ST_GeomFromGeoJSON($3)),
                        'EPSG:4326', 'EPSG:2154'
                    ),
                    ST_Length(
                        ST_Transform(
                            ST_FlipCoordinates(ST_GeomFromGeoJSON($3)),
                            'EPSG:4326', 'EPSG:2154'
                        )
                    ) / 1000.0
                )
                """,
                [line_id, line_name, geom_json],
            )
            inserted += 1

        # Construire les noms de lignes depuis les gares (si deja chargees)
        _build_line_names(conn)

        logger.info(f"Charge {inserted:,} lignes ferroviaires dans ref_railway_lines")
        return inserted


def _build_line_names(conn: duckdb.DuckDBPyConnection) -> None:
    """Construit les noms de lignes depuis les gares associees.

    Pour chaque ligne, prend la premiere et la derniere gare voyageurs
    (par nom alphabetique) et forme "Gare-A — Gare-Z".
    """
    import contextlib

    with contextlib.suppress(Exception):
        conn.execute(
            """
            UPDATE ref_railway_lines SET line_name = sub.label
            FROM (
                SELECT line_code,
                       MIN(station_name) || ' — ' || MAX(station_name) AS label
                FROM ref_railway_stations
                WHERE station_name != ''
                GROUP BY line_code
                HAVING COUNT(DISTINCT station_name) >= 2
            ) sub
            WHERE ref_railway_lines.line_id = sub.line_code
            """
        )


def load_railway_stations(geojson_path: Path) -> int:
    """Charge les gares voyageurs dans ref_railway_stations.

    Proprietes SNCF utilisees :
    - code_uic : identifiant UIC de la gare
    - libelle : nom de la gare
    - code_ligne : code de la ligne RFN associee
    - commune : nom de la commune
    - departemen : nom du departement
    - voyageurs : 'O' si gare voyageurs
    """
    with db_session() as conn:
        data = json.loads(geojson_path.read_text(encoding="utf-8"))
        features = data.get("features", [])

        if not features:
            logger.warning("Aucune feature dans le fichier GeoJSON gares")
            return 0

        conn.execute("DELETE FROM ref_railway_stations")

        inserted = 0
        for feat in features:
            props = feat.get("properties", {})
            geom = feat.get("geometry")
            if not geom or geom.get("type") != "Point":
                continue

            # Ne garder que les gares voyageurs
            if props.get("voyageurs") != "O":
                continue

            coords = geom.get("coordinates", [0, 0])
            lon, lat = float(coords[0]), float(coords[1])

            # Filtrer les gares hors metropole
            if not (41 <= lat <= 52 and -6 <= lon <= 10):
                continue

            station_id = str(props.get("code_uic", ""))
            station_name = str(props.get("libelle", ""))
            line_code = str(props.get("code_ligne", ""))
            commune = str(props.get("commune", ""))
            department = str(props.get("departemen", ""))

            geom_json = json.dumps(geom)

            conn.execute(
                """
                INSERT INTO ref_railway_stations
                    (station_id, station_name, line_code, commune, department,
                     latitude, longitude, geometry)
                VALUES ($1, $2, $3, $4, $5, $6, $7, ST_GeomFromGeoJSON($8))
                """,
                [station_id, station_name, line_code, commune, department, lat, lon, geom_json],
            )
            inserted += 1

        # Construire les noms de lignes
        _build_line_names(conn)

        logger.info(f"Charge {inserted:,} gares dans ref_railway_stations")
        return inserted
