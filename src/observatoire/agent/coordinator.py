"""Agent coordinateur pour l'analyse télécom."""

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from observatoire.agent.sub_agents.analyzer import analyzer_agent
from observatoire.agent.sub_agents.fetcher import fetcher_agent
from observatoire.agent.sub_agents.reporter import reporter_agent


class AnalysisRequest(BaseModel):
    """Requête d'analyse structurée."""

    zone: str = Field(description="Code département ou commune")
    zone_type: str = Field(description="'department' ou 'commune'")
    technology: str = "4G"
    include_comparison: bool = True


class AnalysisReport(BaseModel):
    """Rapport d'analyse structuré."""

    zone: str
    summary: str
    coverage_data: dict
    insights: list[str]
    recommendations: list[str]


coordinator = Agent(
    "anthropic:claude-sonnet-4-20250514",
    defer_model_check=True,
    system_prompt=(
        "Tu es un analyste télécom spécialisé dans la performance "
        "des réseaux mobiles français. Tu analyses les données de couverture ARCEP "
        "et produis des rapports structurés avec des insights actionnables.\n\n"
        "Tu dois :\n"
        "1. Récupérer les données de couverture pour la zone demandée\n"
        "2. Analyser les écarts entre opérateurs\n"
        "3. Identifier les zones sous-couvertes\n"
        "4. Produire un rapport avec des recommandations\n\n"
        "Réponds toujours en français."
    ),
    output_type=AnalysisReport,
)


async def run_analysis(request: AnalysisRequest) -> AnalysisReport:
    """Exécute une analyse complète en orchestrant les sous-agents."""
    # Étape 1 : Récupérer les données
    fetch_result = await fetcher_agent.run(
        f"Récupère les données de couverture {request.technology} "
        f"pour le {request.zone_type} {request.zone}"
    )

    # Étape 2 : Analyser les données
    analysis_result = await analyzer_agent.run(
        f"Analyse ces données de couverture et identifie les insights :\n{fetch_result.output}"
    )

    # Étape 3 : Générer le rapport
    report_result = await reporter_agent.run(
        f"Génère un rapport structuré à partir de cette analyse :\n"
        f"Zone: {request.zone}\n"
        f"Données: {fetch_result.output}\n"
        f"Analyse: {analysis_result.output}"
    )

    # Étape 4 : Structurer le résultat final via le coordinateur
    final = await coordinator.run(
        f"Synthétise ce rapport d'analyse télécom en un AnalysisReport structuré :\n"
        f"{report_result.output}"
    )

    return final.output
