"""Prompts MCP pré-configurés pour l'analyse télécom."""

from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Enregistre les prompts MCP auprès du serveur."""

    @mcp.prompt()
    def analyze_coverage(department_code: str, technology: str = "4G") -> str:
        """Analyse complète de la couverture réseau pour un département.

        Args:
            department_code: Code département (ex: 31)
            technology: Technologie à analyser (2G, 3G, 4G, 5G)
        """
        return (
            f"Analyse la couverture {technology} dans le département {department_code}. "
            f"Utilise l'outil compare_operators pour obtenir les données, puis :\n"
            f"1. Compare les opérateurs entre eux\n"
            f"2. Identifie le meilleur et le moins bon opérateur\n"
            f"3. Calcule l'écart de couverture entre le premier et le dernier\n"
            f"4. Donne des recommandations pour les habitants de ce département"
        )

    @mcp.prompt()
    def coverage_gap_report(commune_code: str) -> str:
        """Rapport sur les lacunes de couverture d'une commune.

        Args:
            commune_code: Code INSEE de la commune
        """
        return (
            f"Génère un rapport détaillé sur la couverture de la commune {commune_code}. "
            f"Utilise l'outil get_coverage pour récupérer les données, puis :\n"
            f"1. Identifie les technologies où la couverture est < 80%\n"
            f"2. Compare avec la moyenne départementale\n"
            f"3. Identifie si c'est une zone blanche ou grise\n"
            f"4. Propose des explications possibles (relief, densité, etc.)"
        )
