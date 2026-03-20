# ADR-002 : FastMCP pour le serveur MCP

## Statut : Accepté (mars 2026)

## Contexte
Le projet expose les données télécom comme tools/resources MCP pour Claude.
Le SDK Python MCP officiel propose deux approches : l'API bas-niveau (Server +
handlers manuels) et l'API haut-niveau (FastMCP avec décorateurs).

## Décision
Utiliser **FastMCP** (API haut-niveau du SDK MCP Python) avec décorateurs
`@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()`.

## Options considérées

| Approche | Avantages | Inconvénients |
|----------|-----------|---------------|
| Server (bas-niveau) | Contrôle total, handlers explicites | Verbeux, boilerplate lourd |
| FastMCP (haut-niveau) | Décorateurs simples, type inference | Moins de contrôle sur les types MCP |

## Conséquences
- **Positif** : code minimal — un décorateur + docstring = tool complet avec schema auto
- **Positif** : les docstrings Python deviennent les descriptions MCP (DRY)
- **Positif** : defer_model_check disponible sur pydantic-ai pour les tests sans API key
- **Attention** : l'API FastMCP a évolué (anciennement `result_type` → `output_type`),
  suivre la doc officielle plutôt que les exemples datés
