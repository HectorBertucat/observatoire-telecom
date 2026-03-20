"""Endpoints de couverture réseau."""

from typing import Annotated

import duckdb
from fastapi import APIRouter, Depends, Query

from observatoire.api.deps import get_db
from observatoire.api.schemas.coverage import CommuneCoverage
from observatoire.db.queries import get_commune_coverage

router = APIRouter()

DB = Annotated[duckdb.DuckDBPyConnection, Depends(get_db)]


@router.get("/commune/{commune_code}", response_model=list[CommuneCoverage])
async def commune_coverage(
    commune_code: str,
    db: DB,
    technology: str = Query("4G", description="Technologie réseau"),
):
    """Retourne la couverture d'une commune pour tous les opérateurs."""
    return get_commune_coverage(db, commune_code, technology)
