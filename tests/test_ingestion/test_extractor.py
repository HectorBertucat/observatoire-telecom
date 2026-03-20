"""Tests pour le module d'extraction."""

from pathlib import Path

from observatoire.ingestion.extractor import extract_7z


def test_extract_7z_skips_if_already_extracted(tmp_path: Path):
    """Vérifie que l'extraction est idempotente."""
    # Simuler un fichier déjà extrait
    gpkg_file = tmp_path / "test.gpkg"
    gpkg_file.write_text("fake gpkg content")

    result = extract_7z(Path("fake_archive.7z"), dest_dir=tmp_path)
    assert result == gpkg_file
