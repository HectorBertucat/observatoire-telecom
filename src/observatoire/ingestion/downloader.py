"""Téléchargement des données sources ARCEP/ANFR."""

import logging
from pathlib import Path

import httpx

from observatoire.config import settings

logger = logging.getLogger(__name__)


# Mapping des fichiers ARCEP à télécharger
ARCEP_COVERAGE_FILES = {
    "bouygues_4g": (
        "couvertures_theoriques/{quarter}/Metropole/00_Metropole/"
        "{quarter}_couv_Metropole_BYT_4G_data.gpkg.7z"
    ),
    "free_4g": (
        "couvertures_theoriques/{quarter}/Metropole/00_Metropole/"
        "{quarter}_couv_Metropole_FREE_4G_data.gpkg.7z"
    ),
    "orange_4g": (
        "couvertures_theoriques/{quarter}/Metropole/00_Metropole/"
        "{quarter}_couv_Metropole_OF_4G_data.gpkg.7z"
    ),
    "sfr_4g": (
        "couvertures_theoriques/{quarter}/Metropole/00_Metropole/"
        "{quarter}_couv_Metropole_SFR_4G_data.gpkg.7z"
    ),
}


async def download_file(url: str, dest: Path) -> Path:
    """Télécharge un fichier avec suivi de progression."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        logger.info(f"Fichier déjà présent : {dest.name}")
        return dest

    logger.info(f"Téléchargement : {url}")
    async with (
        httpx.AsyncClient(follow_redirects=True, timeout=300) as client,
        client.stream("GET", url) as response,
    ):
            response.raise_for_status()
            total = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(dest, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = (downloaded / total) * 100
                        logger.debug(f"  {pct:.1f}% ({downloaded}/{total})")

    logger.info(f"Téléchargé : {dest.name} ({dest.stat().st_size:,} bytes)")
    return dest


async def download_arcep_coverage(quarter: str | None = None) -> list[Path]:
    """Télécharge les fichiers de couverture ARCEP pour un trimestre."""
    quarter = quarter or settings.arcep_quarter
    downloaded: list[Path] = []

    for _key, path_template in ARCEP_COVERAGE_FILES.items():
        relative_path = path_template.format(quarter=quarter)
        url = f"{settings.arcep_base_url}/{relative_path}"
        filename = Path(relative_path).name
        dest = settings.raw_dir / "arcep" / quarter / filename

        path = await download_file(url, dest)
        downloaded.append(path)

    return downloaded
