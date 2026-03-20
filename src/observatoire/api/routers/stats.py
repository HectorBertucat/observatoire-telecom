"""Endpoints statistiques agrégées."""

from typing import Annotated

import duckdb
from fastapi import APIRouter, Depends, Query

from observatoire.api.deps import get_db
from observatoire.db.queries import get_department_stats, get_table_counts

router = APIRouter()

DB = Annotated[duckdb.DuckDBPyConnection, Depends(get_db)]


@router.get("/department/{department_code}")
async def department_stats(
    department_code: str,
    db: DB,
    technology: str = Query("4G", description="Technologie réseau"),
):
    """Retourne les statistiques de couverture par opérateur pour un département."""
    return get_department_stats(db, department_code, technology)


@router.get("/tables")
async def table_counts(db: DB):
    """Retourne le nombre de lignes par table (debug/monitoring)."""
    return get_table_counts(db)
