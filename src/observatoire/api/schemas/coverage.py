"""Schémas Pydantic pour les endpoints de couverture."""

from pydantic import BaseModel, Field


class CommuneCoverage(BaseModel):
    """Couverture d'une commune par opérateur."""

    commune_code: str
    commune_name: str
    operator: str
    technology: str
    coverage_pct: float = Field(..., ge=0, le=100, description="Pourcentage de couverture")
    antenna_count: int
    population: int | None = None


class CoverageComparison(BaseModel):
    """Comparaison de couverture entre opérateurs pour une zone."""

    zone: str
    quarter: str
    operators: list[CommuneCoverage]
