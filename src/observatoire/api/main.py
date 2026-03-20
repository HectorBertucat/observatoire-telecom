"""Point d'entrée de l'API FastAPI."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from observatoire.api.routers import antennas, coverage, stats
from observatoire.api.schemas.common import HealthResponse
from observatoire.db.connection import get_connection
from observatoire.db.schema import create_schema, seed_reference_data

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Gestion du cycle de vie de l'application."""
    # Startup : créer le schéma si nécessaire et vérifier la DB
    conn = get_connection(read_only=False)
    create_schema(conn)
    seed_reference_data(conn)
    tables = conn.execute("SHOW TABLES").fetchall()
    conn.close()
    logger.info(f"Base DuckDB connectée ({len(tables)} tables)")
    yield
    logger.info("API arrêtée proprement")


app = FastAPI(
    title="Observatoire Télécom France",
    description="API d'accès aux données de couverture et qualité des réseaux mobiles français",
    version="0.1.0",
    lifespan=lifespan,
)

# Monter les routers
app.include_router(coverage.router, prefix="/api/v1/coverage", tags=["Couverture"])
app.include_router(antennas.router, prefix="/api/v1/antennas", tags=["Antennes"])
app.include_router(stats.router, prefix="/api/v1/stats", tags=["Statistiques"])


@app.get("/health", response_model=HealthResponse, tags=["Système"])
async def health_check() -> HealthResponse:
    """Vérification de l'état de l'API."""
    conn = get_connection(read_only=True)
    tables = conn.execute("SHOW TABLES").fetchall()
    conn.close()
    return HealthResponse(status="ok", tables=len(tables))


# Servir le frontend statique (APRÈS les routes API pour éviter les conflits)
_frontend_dir = Path(__file__).parent.parent.parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/css", StaticFiles(directory=_frontend_dir / "css"), name="css")
    app.mount("/js", StaticFiles(directory=_frontend_dir / "js"), name="js")
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
