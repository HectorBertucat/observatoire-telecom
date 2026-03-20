"""Tests pour l'API FastAPI."""

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _use_temp_db(tmp_path):
    """Force l'API à utiliser une DB temporaire pour les tests."""
    os.environ["OBS_DB_PATH"] = str(tmp_path / "test.duckdb")
    # Recharger le module config pour prendre en compte le changement
    from observatoire import config

    config.settings = config.Settings()
    yield
    os.environ.pop("OBS_DB_PATH", None)
    config.settings = config.Settings()


@pytest.fixture
def client():
    """Client de test FastAPI."""
    # Import après le changement de config
    from observatoire.api.main import app

    with TestClient(app) as c:
        yield c


def test_health_check(client):
    """Vérifie que le health check retourne 200."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["tables"] >= 0


def test_openapi_docs_accessible(client):
    """Vérifie que la doc OpenAPI est accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Observatoire Télécom France"


def test_coverage_commune_empty(client):
    """Vérifie qu'une commune sans données retourne une liste vide."""
    response = client.get("/api/v1/coverage/commune/99999")
    assert response.status_code == 200
    assert response.json() == []


def test_stats_tables(client):
    """Vérifie que l'endpoint tables retourne les comptages."""
    response = client.get("/api/v1/stats/tables")
    assert response.status_code == 200
    data = response.json()
    assert "ref_operators" in data


def test_stats_coverage(client):
    """Vérifie que l'endpoint coverage stats retourne une liste."""
    response = client.get("/api/v1/stats/coverage?technology=4G")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_coverage_geojson(client):
    """Vérifie que l'endpoint GeoJSON retourne un FeatureCollection."""
    response = client.get("/api/v1/coverage/geojson?operator=OF&technology=4G")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert isinstance(data["features"], list)
