"""Tests pour les endpoints trajets ferroviaires."""

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _use_temp_db(tmp_path):
    """Force l'API a utiliser une DB temporaire pour les tests."""
    os.environ["OBS_DB_PATH"] = str(tmp_path / "test.duckdb")
    from observatoire import config

    config.settings = config.Settings()
    yield
    os.environ.pop("OBS_DB_PATH", None)
    config.settings = config.Settings()


@pytest.fixture
def client():
    """Client de test FastAPI."""
    from observatoire.api.main import app

    with TestClient(app) as c:
        yield c


def test_list_lines_returns_list(client):
    """Verifie que la liste des lignes retourne une liste."""
    response = client.get("/api/v1/routes/lines")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_lines_with_search(client):
    """Verifie le filtre de recherche sur les lignes."""
    response = client.get("/api/v1/routes/lines?search=paris")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_stations_returns_list(client):
    """Verifie que la liste des gares retourne une liste."""
    response = client.get("/api/v1/routes/stations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_route_coverage_returns_list(client):
    """Verifie que l'analyse de couverture retourne une liste (vide si pas de donnees)."""
    response = client.post(
        "/api/v1/routes/coverage",
        json={"line_id": "999999", "technology": "4G"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_line_geojson_returns_feature_collection(client):
    """Verifie que le GeoJSON retourne un FeatureCollection."""
    response = client.get("/api/v1/routes/lines/999999/geojson")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
