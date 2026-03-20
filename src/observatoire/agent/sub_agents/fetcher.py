"""Sous-agent de récupération des données."""

from pydantic_ai import Agent

fetcher_agent = Agent(
    "anthropic:claude-sonnet-4-20250514",
    defer_model_check=True,
    system_prompt=(
        "Tu es un agent spécialisé dans la récupération de données télécom. "
        "Tu extrais et formates les données brutes de couverture réseau. "
        "Retourne les données de manière structurée et lisible. "
        "Réponds en français."
    ),
)
