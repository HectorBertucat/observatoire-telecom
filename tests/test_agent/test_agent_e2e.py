"""Tests E2E de l'agent coordinateur avec TestModel (sans clé API)."""

import pytest
from pydantic_ai.models.test import TestModel

from observatoire.agent.coordinator import (
    AnalysisReport,
    AnalysisRequest,
    coordinator,
)
from observatoire.agent.sub_agents.analyzer import analyzer_agent
from observatoire.agent.sub_agents.fetcher import fetcher_agent
from observatoire.agent.sub_agents.reporter import reporter_agent


@pytest.fixture
def _patch_agents():
    """Remplace les modèles Claude par TestModel pour les tests."""
    test_model = TestModel()
    with (
        coordinator.override(model=test_model),
        fetcher_agent.override(model=test_model),
        analyzer_agent.override(model=test_model),
        reporter_agent.override(model=test_model),
    ):
        yield


async def test_fetcher_agent_runs(_patch_agents):
    """Vérifie que le fetcher agent s'exécute sans erreur."""
    result = await fetcher_agent.run("Récupère les données 4G pour Toulouse")
    assert result.output is not None
    assert isinstance(result.output, str)


async def test_analyzer_agent_runs(_patch_agents):
    """Vérifie que l'analyzer agent s'exécute sans erreur."""
    result = await analyzer_agent.run("Analyse ces données de couverture")
    assert result.output is not None


async def test_reporter_agent_runs(_patch_agents):
    """Vérifie que le reporter agent s'exécute sans erreur."""
    result = await reporter_agent.run("Génère un rapport")
    assert result.output is not None


async def test_coordinator_produces_structured_report(_patch_agents):
    """Vérifie que le coordinateur produit un AnalysisReport structuré."""
    result = await coordinator.run(
        "Analyse la couverture 4G dans le département 31"
    )
    report = result.output
    assert isinstance(report, AnalysisReport)
    assert report.zone is not None
    assert isinstance(report.insights, list)
    assert isinstance(report.recommendations, list)


def test_analysis_request_validation():
    """Vérifie la validation du modèle de requête."""
    req = AnalysisRequest(zone="31", zone_type="department")
    assert req.technology == "4G"
    assert req.include_comparison is True

    req2 = AnalysisRequest(
        zone="31555", zone_type="commune", technology="5G", include_comparison=False
    )
    assert req2.technology == "5G"
