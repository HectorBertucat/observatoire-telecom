FROM python:3.12-slim

# Dépendances système pour DuckDB spatial (GDAL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    p7zip-full \
    && rm -rf /var/lib/apt/lists/*

# Installer uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copier les fichiers de dépendances d'abord (cache Docker)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copier le code source
COPY src/ src/
COPY frontend/ frontend/

# Port de l'API
EXPOSE 8000

# Lancer l'API en production
CMD ["uv", "run", "uvicorn", "observatoire.api.main:app", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
