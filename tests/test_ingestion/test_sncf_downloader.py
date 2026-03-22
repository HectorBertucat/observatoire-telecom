"""Tests pour le module de telechargement SNCF."""

from observatoire.ingestion.sncf_downloader import (
    get_sncf_lines_url,
    get_sncf_stations_url,
)


def test_sncf_lines_url():
    """Verifie que l'URL des lignes RFN est correcte."""
    url = get_sncf_lines_url()
    assert "ressources.data.sncf.com" in url
    assert "formes-des-lignes-du-rfn" in url
    assert url.endswith("/geojson")


def test_sncf_stations_url():
    """Verifie que l'URL des gares est correcte."""
    url = get_sncf_stations_url()
    assert "ressources.data.sncf.com" in url
    assert "liste-des-gares" in url
    assert url.endswith("/geojson")
