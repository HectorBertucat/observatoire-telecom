.PHONY: help pipeline ingest serve test lint format mcp seed tiles sncf clean

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

pipeline: ## Pipeline complète : download ARCEP + load + generate tiles
	uv run python scripts/run_full_pipeline.py orange bouygues free sfr
	uv run python scripts/generate_tiles.py

ingest: ## Lance le pipeline d'ingestion complet
	uv run python -m observatoire.ingestion.loader

serve: ## Lance l'API en mode développement
	uv run uvicorn observatoire.api.main:app --reload --host 0.0.0.0 --port 8000

test: ## Lance les tests
	uv run pytest -v

lint: ## Vérifie le code (ruff + mypy)
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/
	uv run mypy src/

format: ## Formate le code automatiquement
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

mcp: ## Lance le serveur MCP
	uv run python -m observatoire.mcp

seed: ## Génère des données de test (sans téléchargement)
	uv run python scripts/seed_sample_data.py

sncf: ## Télécharge et charge les données SNCF (lignes RFN + gares)
	uv run python scripts/load_sncf_data.py

tiles: ## Régénère les vector tiles PMTiles
	uv run python scripts/generate_tiles.py

clean: ## Nettoie les fichiers temporaires
	rm -rf data/raw/* data/processed/*
	find . -type d -name __pycache__ -exec rm -rf {} +
