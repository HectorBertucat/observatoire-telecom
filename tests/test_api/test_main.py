"""Tests pour l'API FastAPI."""

import pytest
from fastapi.testclient import TestClient

from observatoire.api.main import app


@pytest.fixture
def client():
    """Client de test FastAPI."""
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
