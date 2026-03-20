"""Tests pour les endpoints antennes."""

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _use_temp_db(tmp_path):
    """Force l'API à utiliser une DB temporaire pour les tests."""
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


def test_antenna_stats_returns_list(client):
    """Vérifie que les stats antennes retournent une liste."""
    response = client.get("/api/v1/antennas/stats")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_antenna_stats_with_operator_filter(client):
    """Vérifie le filtre par opérateur."""
    response = client.get("/api/v1/antennas/stats?operator=OF")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_antenna_list_returns_list(client):
    """Vérifie que la liste d'antennes retourne une liste."""
    response = client.get("/api/v1/antennas/?limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_antenna_list_with_filters(client):
    """Vérifie les filtres combinés."""
    response = client.get("/api/v1/antennas/?operator=OF&technology=4G&limit=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_stats_antennas_endpoint(client):
    """Vérifie l'endpoint stats/antennas."""
    response = client.get("/api/v1/stats/antennas")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
