"""Telechargement des donnees SNCF Open Data (lignes RFN + gares)."""

import logging
from pathlib import Path

from observatoire.config import settings
from observatoire.ingestion.downloader import download_file

logger = logging.getLogger(__name__)


def get_sncf_lines_url() -> str:
    """Retourne l'URL de telechargement des lignes RFN."""
    return settings.sncf_lines_url


def get_sncf_stations_url() -> str:
    """Retourne l'URL de telechargement des gares."""
    return settings.sncf_stations_url


async def download_sncf_lines() -> Path:
    """Telecharge le GeoJSON des lignes du Reseau Ferre National."""
    url = get_sncf_lines_url()
    dest = settings.raw_dir / "sncf" / "formes-des-lignes-du-rfn.geojson"
    return await download_file(url, dest)


async def download_sncf_stations() -> Path:
    """Telecharge le GeoJSON des gares voyageurs."""
    url = get_sncf_stations_url()
    dest = settings.raw_dir / "sncf" / "liste-des-gares.geojson"
    return await download_file(url, dest)
