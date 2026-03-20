"""Génère des données de test dans DuckDB sans télécharger les sources ARCEP/ANFR.

Utile pour :
- Le CI/CD (pas de téléchargement de 1 GB)
- Les développeurs qui clonent le repo
- Les tests d'intégration
"""

import logging

from observatoire.db.connection import db_session
from observatoire.db.schema import create_schema, seed_reference_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Quelques communes représentatives
SAMPLE_COMMUNES = [
    ("31555", "Toulouse", "31"),
    ("75056", "Paris", "75"),
    ("69123", "Lyon", "69"),
    ("13055", "Marseille", "13"),
    ("33063", "Bordeaux", "33"),
    ("44109", "Nantes", "44"),
    ("67482", "Strasbourg", "67"),
    ("59350", "Lille", "59"),
]

OPERATORS = ["OF", "BYT", "FREE", "SFR"]
TECHNOLOGIES = ["2G", "3G", "4G", "5G"]


def seed_sample_antennas() -> int:
    """Insère des données d'antennes fictives pour les tests."""
    with db_session() as conn:
        create_schema(conn)
        seed_reference_data(conn)

        # Vérifier si déjà peuplé
        count = conn.execute("SELECT COUNT(*) FROM raw_antenna_sites").fetchone()[0]  # type: ignore[index]
        if count > 0:
            logger.info(f"raw_antenna_sites déjà peuplé ({count:,} lignes), skip.")
            return count

        logger.info("Insertion de données d'antennes fictives...")

        inserted = 0
        site_id = 1

        for commune_code, commune_name, dept in SAMPLE_COMMUNES:
            # Coordonnées approximatives par commune
            base_coords = {
                "31555": (43.6047, 1.4442),
                "75056": (48.8566, 2.3522),
                "69123": (45.7640, 4.8357),
                "13055": (43.2965, 5.3698),
                "33063": (44.8378, -0.5792),
                "44109": (47.2184, -1.5536),
                "67482": (48.5734, 7.7521),
                "59350": (50.6292, 3.0573),
            }
            lat, lon = base_coords.get(commune_code, (46.0, 2.0))

            for operator in OPERATORS:
                for tech in TECHNOLOGIES:
                    # 3-8 antennes par opérateur×techno×commune
                    n_sites = 3 + hash(f"{commune_code}{operator}{tech}") % 6
                    for i in range(n_sites):
                        offset_lat = (i * 0.003) - 0.01
                        offset_lon = (i * 0.004) - 0.01
                        conn.execute(
                            """
                            INSERT INTO raw_antenna_sites
                                (id, operator, latitude, longitude,
                                 commune_code, commune_name, department_code,
                                 technology, geometry)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?,
                                    ST_Point(?, ?))
                            """,
                            [
                                site_id,
                                operator,
                                lat + offset_lat,
                                lon + offset_lon,
                                commune_code,
                                commune_name,
                                dept,
                                tech,
                                lon + offset_lon,
                                lat + offset_lat,
                            ],
                        )
                        site_id += 1
                        inserted += 1

        logger.info(f"Inséré {inserted:,} antennes fictives dans {len(SAMPLE_COMMUNES)} communes")
        return inserted


if __name__ == "__main__":
    count = seed_sample_antennas()
    logger.info(f"Done: {count:,} antennes en base.")
