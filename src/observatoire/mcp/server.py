"""Serveur MCP pour l'Observatoire Télécom."""

from mcp.server.fastmcp import FastMCP

from observatoire.mcp.prompts import register_prompts
from observatoire.mcp.resources import register_resources
from observatoire.mcp.tools import register_tools

mcp = FastMCP(
    "observatoire-telecom",
    instructions=(
        "Serveur MCP pour interroger les données de couverture et qualité "
        "des réseaux mobiles en France (données ARCEP/ANFR)."
    ),
)

register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)


def main() -> None:
    """Point d'entrée du serveur MCP."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
