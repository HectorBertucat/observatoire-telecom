"""Endpoints statistiques agrégées."""

from typing import Annotated

import duckdb
from fastapi import APIRouter, Depends, Query

from observatoire.api.deps import get_db
from observatoire.db.queries import get_raw_coverage_stats, get_table_counts

router = APIRouter()

DB = Annotated[duckdb.DuckDBPyConnection, Depends(get_db)]


@router.get("/coverage")
async def coverage_stats(
    db: DB,
    technology: str = Query("4G", description="Technologie réseau"),
):
    """Retourne les stats de couverture par opérateur depuis les données brutes."""
    return get_raw_coverage_stats(db, technology)


@router.get("/tables")
async def table_counts(db: DB):
    """Retourne le nombre de lignes par table (debug/monitoring)."""
    return get_table_counts(db)
