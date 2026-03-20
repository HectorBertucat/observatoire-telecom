"""Téléchargement des données sources ARCEP/ANFR."""

import logging
from pathlib import Path

import httpx

from observatoire.config import settings

logger = logging.getLogger(__name__)


# Mapping code opérateur interne → code fichier ARCEP
OPERATOR_FILE_CODES = {
    "bouygues": "BOUY",
    "free": "FREE",
    "orange": "OF",
    "sfr": "SFR0",
}

# Mapping code fichier ARCEP → code interne DB (ref_operators)
ARCEP_TO_DB_OPERATOR = {
    "BOUY": "BYT",
    "FREE": "FREE",
    "OF": "OF",
    "SFR0": "SFR",
}

# Template de chemin pour les fichiers de couverture
COVERAGE_PATH_TEMPLATE = (
    "couvertures_theoriques/{quarter}/Metropole/00_Metropole/"
    "{quarter}_couv_Metropole_{operator_code}_{technology}_data.gpkg.7z"
)


def get_coverage_url(operator: str, technology: str = "4G", quarter: str | None = None) -> str:
    """Construit l'URL de téléchargement pour un opérateur et une technologie."""
    quarter = quarter or settings.arcep_quarter
    operator_code = OPERATOR_FILE_CODES[operator]
    relative_path = COVERAGE_PATH_TEMPLATE.format(
        quarter=quarter, operator_code=operator_code, technology=technology
    )
    return f"{settings.arcep_base_url}/{relative_path}"


async def download_file(url: str, dest: Path) -> Path:
    """Télécharge un fichier avec suivi de progression."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        logger.info(f"Fichier déjà présent : {dest.name}")
        return dest

    logger.info(f"Téléchargement : {url}")
    async with (
        httpx.AsyncClient(follow_redirects=True, timeout=600) as client,
        client.stream("GET", url) as response,
    ):
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(dest, "wb") as f:
            async for chunk in response.aiter_bytes(chunk_size=65536):
                f.write(chunk)
                downloaded += len(chunk)
                if total and downloaded % (5 * 1024 * 1024) < 65536:
                    pct = (downloaded / total) * 100
                    dl_mb = downloaded // (1024 * 1024)
                    total_mb = total // (1024 * 1024)
                    logger.info(f"  {pct:.0f}% ({dl_mb} / {total_mb} MB)")

    logger.info(f"Téléchargé : {dest.name} ({dest.stat().st_size // (1024 * 1024)} MB)")
    return dest


async def download_arcep_coverage(
    operators: list[str] | None = None,
    technology: str = "4G",
    quarter: str | None = None,
) -> list[Path]:
    """Télécharge les fichiers de couverture ARCEP pour un trimestre.

    Args:
        operators: Liste d'opérateurs à télécharger (tous si None)
        technology: Technologie réseau (2G, 3G, 4G, 5G)
        quarter: Trimestre ARCEP (ex: 2025_T3)
    """
    quarter = quarter or settings.arcep_quarter
    operators = operators or list(OPERATOR_FILE_CODES.keys())
    downloaded: list[Path] = []

    for operator in operators:
        url = get_coverage_url(operator, technology, quarter)
        filename = Path(url).name
        dest = settings.raw_dir / "arcep" / quarter / filename

        path = await download_file(url, dest)
        downloaded.append(path)

    return downloaded
