"""Tests pour le serveur MCP."""

from observatoire.mcp.server import mcp


def test_mcp_server_has_name():
    """Vérifie que le serveur MCP est correctement initialisé."""
    assert mcp.name == "observatoire-telecom"


async def test_mcp_lists_tools():
    """Vérifie que les tools MCP sont enregistrés."""
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "get_antenna_count" in tool_names
    assert "compare_operators" in tool_names
    assert "get_coverage_summary" in tool_names
    assert "search_antennas" in tool_names


async def test_mcp_lists_prompts():
    """Vérifie que les prompts MCP sont enregistrés."""
    prompts = await mcp.list_prompts()
    prompt_names = [p.name for p in prompts]
    assert "analyze_coverage" in prompt_names
    assert "coverage_gap_report" in prompt_names
