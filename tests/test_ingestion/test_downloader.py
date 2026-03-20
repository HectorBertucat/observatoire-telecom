"""Tests pour le module de téléchargement."""

from observatoire.ingestion.downloader import (
    ARCEP_TO_DB_OPERATOR,
    OPERATOR_FILE_CODES,
    get_coverage_url,
)


def test_all_operators_have_file_codes():
    """Vérifie que les 4 opérateurs métropolitains sont couverts."""
    expected = {"bouygues", "free", "orange", "sfr"}
    assert set(OPERATOR_FILE_CODES.keys()) == expected


def test_all_file_codes_map_to_db_codes():
    """Vérifie que chaque code fichier ARCEP a un code DB."""
    for file_code in OPERATOR_FILE_CODES.values():
        assert file_code in ARCEP_TO_DB_OPERATOR


def test_coverage_url_format():
    """Vérifie que les URLs générées sont valides."""
    url = get_coverage_url("orange", "4G", "2025_T3")
    assert "2025_T3" in url
    assert "OF" in url
    assert url.endswith(".gpkg.7z")
    assert "Metropole" in url


def test_coverage_url_all_operators():
    """Vérifie que chaque opérateur produit une URL distincte."""
    urls = set()
    for operator in OPERATOR_FILE_CODES:
        url = get_coverage_url(operator, "4G", "2025_T3")
        urls.add(url)
    assert len(urls) == 4
