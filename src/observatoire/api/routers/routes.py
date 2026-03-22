"""Endpoints trajets ferroviaires et couverture."""

from typing import Annotated, Any

import duckdb
from fastapi import APIRouter, Depends, Query

from observatoire.api.deps import get_db
from observatoire.api.schemas.routes import RouteCoverageRequest
from observatoire.db.queries import (
    find_transfer_options,
    get_railway_lines,
    get_railway_stations,
    get_route_coverage,
    get_route_geojson,
    get_route_segment_geojson,
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
    """Analyse la couverture reseau le long d'une ligne ferroviaire."""
    return get_route_coverage(db, body.line_id, body.technology, body.buffer_km)


@router.get("/transfers")
async def transfer_options(
    db: DB,
    dep_lines: str = Query(..., description="Codes lignes depart (virgule)"),
    arr_lines: str = Query(..., description="Codes lignes arrivee (virgule)"),
    dep_lat: float = Query(..., description="Latitude gare depart"),
    dep_lon: float = Query(..., description="Longitude gare depart"),
    arr_lat: float = Query(..., description="Latitude gare arrivee"),
    arr_lon: float = Query(..., description="Longitude gare arrivee"),
) -> list[dict[str, Any]]:
    """Trouve les correspondances entre depart et arrivee."""
    dep = [c.strip() for c in dep_lines.split(",") if c.strip()]
    arr = [c.strip() for c in arr_lines.split(",") if c.strip()]
    return find_transfer_options(db, dep, arr, dep_lat, dep_lon, arr_lat, arr_lon)


@router.get("/segment")
async def route_segment(
    db: DB,
    line_id: str = Query(..., description="Code ligne"),
    from_lat: float = Query(..., description="Latitude point depart"),
    from_lon: float = Query(..., description="Longitude point depart"),
    to_lat: float = Query(..., description="Latitude point arrivee"),
    to_lon: float = Query(..., description="Longitude point arrivee"),
) -> dict[str, Any]:
    """Retourne le GeoJSON d'un segment de ligne entre deux points."""
    return get_route_segment_geojson(db, line_id, from_lat, from_lon, to_lat, to_lon)


@router.get("/lines/{line_id}/geojson")
async def line_geojson(
    line_id: str,
    db: DB,
) -> dict[str, Any]:
    """Retourne le GeoJSON complet d'une ligne ferroviaire."""
    return get_route_geojson(db, line_id)
