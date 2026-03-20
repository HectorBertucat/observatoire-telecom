"""Extraction des archives téléchargées."""

import logging
import subprocess
from pathlib import Path

from observatoire.config import settings

logger = logging.getLogger(__name__)


def extract_7z(archive: Path, dest_dir: Path | None = None) -> Path:
    """Extrait une archive .7z et retourne le chemin du fichier extrait."""
    dest_dir = dest_dir or settings.processed_dir / archive.stem
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Vérifier si déjà extrait (chercher un .gpkg)
    existing = list(dest_dir.glob("*.gpkg"))
    if existing:
        logger.info(f"Déjà extrait : {existing[0].name}")
        return existing[0]

    logger.info(f"Extraction : {archive.name} → {dest_dir}")
    result = subprocess.run(
        ["7z", "x", "-y", f"-o{dest_dir}", str(archive)],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Erreur extraction 7z : {result.stderr}")

    extracted = list(dest_dir.glob("*.gpkg"))
    if not extracted:
        raise FileNotFoundError(f"Aucun .gpkg trouvé après extraction de {archive.name}")

    logger.info(f"Extrait : {extracted[0].name}")
    return extracted[0]
