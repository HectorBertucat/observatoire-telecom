"""Endpoints trajets ferroviaires et couverture."""

from typing import Annotated, Any

import duckdb
from fastapi import APIRouter, Depends, Query

from observatoire.api.deps import get_db
from observatoire.api.schemas.routes import RouteCoverageRequest
from observatoire.db.queries import (
    get_railway_lines,
    get_railway_stations,
    get_route_coverage,
    get_route_geojson,
)

router = APIRouter()

DB = Annotated[duckdb.DuckDBPyConnection, Depends(get_db)]


@router.get("/lines")
async def list_lines(
    db: DB,
    search: str | None = Query(None, description="Recherche par nom ou code ligne"),
    limit: int = Query(50, ge=1, le=200),
) -> list[dict[str, Any]]:
    """Liste les lignes ferroviaires du RFN."""
    return get_railway_lines(db, search, limit)


@router.get("/stations")
async def list_stations(
    db: DB,
    search: str | None = Query(None, description="Recherche par nom de gare"),
    limit: int = Query(20, ge=1, le=100),
) -> list[dict[str, Any]]:
    """Liste les gares voyageurs (autocomplete)."""
    return get_railway_stations(db, search, limit)


@router.post("/coverage")
async def route_coverage(
    body: RouteCoverageRequest,
    db: DB,
) -> list[dict[str, Any]]:
    """Analyse la couverture reseau le long d'une ligne ferroviaire.

    Calcule le pourcentage de couverture par operateur en creant un
    buffer autour du trace et en l'intersectant avec les polygones
    de couverture ARCEP.
    """
    return get_route_coverage(db, body.line_id, body.technology, body.buffer_km)


@router.get("/lines/{line_id}/geojson")
async def line_geojson(
    line_id: str,
    db: DB,
) -> dict[str, Any]:
    """Retourne le GeoJSON d'une ligne ferroviaire (pour affichage carte)."""
    return get_route_geojson(db, line_id)
