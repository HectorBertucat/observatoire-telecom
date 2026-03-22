"""Configuration centralisée de l'application."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration centralisée de l'application."""

    # Chemins
    project_root: Path = Path(__file__).parent.parent.parent
    data_dir: Path = project_root / "data"
    raw_dir: Path = data_dir / "raw"
    processed_dir: Path = data_dir / "processed"
    db_path: Path = data_dir / "observatoire.duckdb"

    # Sources ARCEP
    arcep_base_url: str = "https://data.arcep.fr/mobile"
    arcep_quarter: str = "2025_T3"

    # ANFR
    anfr_base_url: str = "https://data.anfr.fr/api"

    # SNCF Open Data
    sncf_lines_url: str = (
        "https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/"
        "formes-des-lignes-du-rfn/exports/geojson"
    )
    sncf_stations_url: str = (
        "https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/"
        "liste-des-gares/exports/geojson"
    )

    # Anthropic (pour l'agent, Phase 5)
    anthropic_api_key: str = ""

    model_config = {"env_file": ".env", "env_prefix": "OBS_"}


settings = Settings()
