"""Schémas Pydantic pour les endpoints antennes."""

from pydantic import BaseModel


class AntennaSite(BaseModel):
    """Site d'antenne simplifié."""

    id: int
    operator: str
    latitude: float
    longitude: float
    commune_code: str
    commune_name: str
    technology: str
    frequency_band: str | None = None
