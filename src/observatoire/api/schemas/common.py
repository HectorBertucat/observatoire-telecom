"""Schémas Pydantic partagés (pagination, filtres)."""

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Paramètres de pagination."""

    offset: int = Field(0, ge=0, description="Nombre d'éléments à sauter")
    limit: int = Field(50, ge=1, le=500, description="Nombre d'éléments à retourner")


class HealthResponse(BaseModel):
    """Réponse du health check."""

    status: str = "ok"
    tables: int = 0
    version: str = "0.1.0"
