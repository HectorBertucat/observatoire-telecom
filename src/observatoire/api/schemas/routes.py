"""Schemas Pydantic pour les trajets ferroviaires."""

from pydantic import BaseModel, Field


class RouteCoverageRequest(BaseModel):
    """Requete d'analyse de couverture le long d'une ligne."""

    line_id: str = Field(..., description="Identifiant de la ligne RFN")
    technology: str = Field("4G", description="Technologie reseau (2G, 3G, 4G)")
    buffer_km: float = Field(
        2.0,
        ge=0.1,
        le=10.0,
        description="Rayon du buffer autour du trace en km",
    )


class RouteCoverageResult(BaseModel):
    """Resultat de couverture pour un operateur le long d'un trajet."""

    operator: str
    operator_name: str | None = None
    total_length_km: float
    covered_length_km: float
    coverage_pct: float
