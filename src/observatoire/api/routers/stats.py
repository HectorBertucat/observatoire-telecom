"""Endpoints statistiques agrégées."""

from typing import Annotated, Any

import duckdb
from fastapi import APIRouter, Depends, Query

from observatoire.api.deps import get_db
from observatoire.db.queries import (
    get_antenna_stats,
    get_raw_coverage_stats,
    get_table_counts,
    list_departments,
)

router = APIRouter()

DB = Annotated[duckdb.DuckDBPyConnection, Depends(get_db)]


@router.get("/coverage")
async def coverage_stats(
    db: DB,
    technology: str = Query("4G", description="Technologie réseau"),
) -> list[dict[str, Any]]:
    """Retourne les stats de couverture par opérateur."""
    return get_raw_coverage_stats(db, technology)


@router.get("/antennas")
async def antenna_stats(
    db: DB,
    operator: str | None = Query(None, description="Code opérateur"),
) -> list[dict[str, Any]]:
    """Retourne les stats d'antennes par opérateur et technologie."""
    return get_antenna_stats(db, operator)


@router.get("/departments")
async def departments(db: DB) -> list[dict[str, Any]]:
    """Liste des départements avec nombre d'antennes."""
    return list_departments(db)


@router.get("/tables")
async def table_counts(db: DB) -> dict[str, int]:
    """Retourne le nombre de lignes par table (debug/monitoring)."""
    return get_table_counts(db)
