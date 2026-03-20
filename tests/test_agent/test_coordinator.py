"""Tests pour l'agent coordinateur."""

from observatoire.agent.coordinator import AnalysisReport, AnalysisRequest, coordinator


def test_analysis_request_defaults():
    """Vérifie les valeurs par défaut de la requête d'analyse."""
    request = AnalysisRequest(zone="31", zone_type="department")
    assert request.technology == "4G"
    assert request.include_comparison is True


def test_analysis_report_schema():
    """Vérifie que le modèle AnalysisReport est valide."""
    report = AnalysisReport(
        zone="31",
        summary="Test summary",
        coverage_data={"orange": 95.2},
        insights=["Insight 1"],
        recommendations=["Recommendation 1"],
    )
    assert report.zone == "31"
    assert len(report.insights) == 1


def test_coordinator_agent_configured():
    """Vérifie que l'agent coordinateur est correctement configuré."""
    assert coordinator.output_type == AnalysisReport
