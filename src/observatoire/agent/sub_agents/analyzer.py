"""Sous-agent d'analyse des données."""

from pydantic_ai import Agent

analyzer_agent = Agent(
    "anthropic:claude-sonnet-4-20250514",
    defer_model_check=True,
    system_prompt=(
        "Tu es un analyste de données télécom. "
        "Tu reçois des données de couverture réseau et tu identifies :\n"
        "- Les écarts significatifs entre opérateurs\n"
        "- Les zones sous-couvertes (< 80%)\n"
        "- Les tendances et anomalies\n"
        "- Les corrélations intéressantes\n\n"
        "Sois factuel et précis dans ton analyse. Réponds en français."
    ),
)
