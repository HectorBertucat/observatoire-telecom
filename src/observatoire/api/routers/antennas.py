"""Endpoints antennes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_antennas():
    """Liste les sites d'antennes (placeholder)."""
    return {"message": "Endpoint antennes - à implémenter avec les données ANFR"}
