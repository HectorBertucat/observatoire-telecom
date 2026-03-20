"""Templates de prompts pour l'analyse télécom."""

COVERAGE_ANALYSIS_PROMPT = """
<context>
Tu analyses la couverture réseau mobile pour le {zone_type} {zone}.
Technologie : {technology}
Données disponibles : couverture par opérateur, nombre d'antennes, population.
</context>

<task>
1. Récupère les données de couverture pour cette zone
2. Compare les opérateurs (couverture moyenne, nombre d'antennes)
3. Identifie les communes les moins bien couvertes
4. Produis un rapport avec insights et recommandations
</task>

<output_format>
Retourne un JSON structuré avec les champs :
- zone: identifiant de la zone
- summary: résumé en 2-3 phrases
- coverage_data: données brutes par opérateur
- insights: liste de constats factuels
- recommendations: liste de recommandations actionnables
</output_format>
"""

COMPARISON_PROMPT = """
<context>
Compare les opérateurs mobiles dans le département {department_code}.
Technologie : {technology}
</context>

<task>
Classe les opérateurs du meilleur au moins bon en termes de :
1. Couverture moyenne (%)
2. Nombre d'antennes déployées
3. Nombre de communes couvertes
Identifie l'écart entre le premier et le dernier.
</task>
"""
