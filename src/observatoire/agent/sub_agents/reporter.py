"""Sous-agent de génération de rapports."""

from pydantic_ai import Agent

reporter_agent = Agent(
    "anthropic:claude-sonnet-4-20250514",
    defer_model_check=True,
    system_prompt=(
        "Tu es un rédacteur de rapports télécom. "
        "Tu transformes des analyses en rapports clairs et actionnables.\n\n"
        "Structure tes rapports avec :\n"
        "- Un résumé exécutif (2-3 phrases)\n"
        "- Les données clés\n"
        "- Les insights principaux\n"
        "- Des recommandations concrètes\n\n"
        "Utilise un ton professionnel. Réponds en français."
    ),
)
