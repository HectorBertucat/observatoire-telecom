"""Tests pour le module de téléchargement."""

from observatoire.ingestion.downloader import ARCEP_COVERAGE_FILES


def test_arcep_urls_are_well_formed():
    """Vérifie que les templates d'URLs ARCEP sont valides."""
    quarter = "2025_T3"
    for _key, template in ARCEP_COVERAGE_FILES.items():
        url = template.format(quarter=quarter)
        assert quarter in url
        assert url.endswith(".7z")
        assert "Metropole" in url


def test_operator_keys_are_complete():
    """Vérifie que les 4 opérateurs métropolitains sont couverts."""
    operators = set(ARCEP_COVERAGE_FILES.keys())
    expected = {"bouygues_4g", "free_4g", "orange_4g", "sfr_4g"}
    assert operators == expected
