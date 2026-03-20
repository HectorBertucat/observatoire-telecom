"""Point d'entrée principal : lance l'API en mode développement."""

import uvicorn


def main() -> None:
    """Lance le serveur FastAPI."""
    uvicorn.run(
        "observatoire.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
