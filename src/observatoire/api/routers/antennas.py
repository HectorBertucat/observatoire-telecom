"""Endpoints antennes ANFR."""

import csv
import io
from typing import Annotated, Any

import duckdb
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from observatoire.api.deps import get_db
from observatoire.db.queries import (
    get_antenna_list,
    get_antenna_stats,
    get_department_antenna_stats,
    get_nearby_antennas,
    search_commune_antennas,
)

router = APIRouter()

DB = Annotated[duckdb.DuckDBPyConnection, Depends(get_db)]


@router.get("/stats")
async def antenna_stats(
    db: DB,
    operator: str | None = Query(None, description="Code opérateur (BYT, FREE, OF, SFR)"),
) -> list[dict[str, Any]]:
    """Retourne le nombre de sites par opérateur et technologie."""
    return get_antenna_stats(db, operator)


@router.get("/department/{department_code}")
async def department_antennas(
    department_code: str,
    db: DB,
) -> list[dict[str, Any]]:
    """Stats d'antennes par opérateur et techno pour un département."""
    return get_department_antenna_stats(db, department_code)


@router.get("/commune/{commune_code}")
async def commune_antennas(
    commune_code: str,
    db: DB,
) -> dict[str, Any]:
    """Résumé des antennes pour une commune (code INSEE)."""
    return search_commune_antennas(db, commune_code)


@router.get("/nearby")
async def nearby_antennas(
    db: DB,
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius: float = Query(2.0, ge=0.1, le=50, description="Rayon en km"),
    technology: str | None = Query(None, description="Technologie (2G, 3G, 4G, 5G)"),
    limit: int = Query(50, ge=1, le=200),
) -> list[dict[str, Any]]:
    """Antennes proches d'un point GPS, triées par distance."""
    return get_nearby_antennas(db, lat, lon, radius, technology, limit)


@router.get("/export.csv")
async def export_antennas_csv(
    db: DB,
    department: str | None = Query(None, description="Code département"),
    operator: str | None = Query(None, description="Code opérateur"),
    technology: str | None = Query(None, description="Technologie"),
) -> StreamingResponse:
    """Exporte les antennes en CSV (max 10 000 lignes)."""
    data = get_antenna_list(db, operator, technology, None, limit=10000, offset=0)

    if department:
        data = [d for d in data if str(d.get("commune_code", "")).startswith(department)]

    output = io.StringIO()
    if data:
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    output.seek(0)
    filename = f"antennes_{department or 'france'}_{operator or 'all'}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/")
async def list_antennas(
    db: DB,
    operator: str | None = Query(None, description="Code opérateur"),
    technology: str | None = Query(None, description="Technologie (2G, 3G, 4G, 5G)"),
    commune: str | None = Query(None, description="Code INSEE commune"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> list[dict[str, Any]]:
    """Liste les sites d'antennes avec filtres et pagination."""
    return get_antenna_list(db, operator, technology, commune, limit, offset)
