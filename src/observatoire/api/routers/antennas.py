"""Endpoints antennes ANFR."""

from typing import Annotated

import duckdb
from fastapi import APIRouter, Depends, Query

from observatoire.api.deps import get_db
from observatoire.db.queries import get_antenna_list, get_antenna_stats

router = APIRouter()

DB = Annotated[duckdb.DuckDBPyConnection, Depends(get_db)]


@router.get("/stats")
async def antenna_stats(
    db: DB,
    operator: str | None = Query(None, description="Code opérateur (BYT, FREE, OF, SFR)"),
):
    """Retourne le nombre de sites par opérateur et technologie."""
    return get_antenna_stats(db, operator)


@router.get("/")
async def list_antennas(
    db: DB,
    operator: str | None = Query(None, description="Code opérateur"),
    technology: str | None = Query(None, description="Technologie (2G, 3G, 4G, 5G)"),
    commune: str | None = Query(None, description="Code INSEE commune"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Liste les sites d'antennes avec filtres et pagination."""
    return get_antenna_list(db, operator, technology, commune, limit, offset)
