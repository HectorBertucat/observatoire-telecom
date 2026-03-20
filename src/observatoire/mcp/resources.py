"""Resources MCP pour exposer les données télécom."""

from mcp.server.fastmcp import FastMCP

from observatoire.db.connection import db_session


def register_resources(mcp: FastMCP) -> None:
    """Enregistre les resources MCP auprès du serveur."""

    @mcp.resource("telecom://operators")
    def list_operators() -> str:
        """Liste des opérateurs mobiles français avec leurs codes."""
        with db_session(read_only=True) as conn:
            result = conn.execute(
                "SELECT code, name FROM ref_operators ORDER BY name"
            ).fetchall()

        if not result:
            return "Aucun opérateur en base."

        lines = ["Opérateurs mobiles français:\n"]
        for row in result:
            lines.append(f"  {row[0]}: {row[1]}")
        return "\n".join(lines)

    @mcp.resource("telecom://technologies")
    def list_technologies() -> str:
        """Liste des technologies réseau disponibles."""
        with db_session(read_only=True) as conn:
            result = conn.execute(
                "SELECT code, description FROM ref_technologies ORDER BY generation"
            ).fetchall()

        if not result:
            return "Aucune technologie en base."

        lines = ["Technologies réseau:\n"]
        for row in result:
            lines.append(f"  {row[0]}: {row[1]}")
        return "\n".join(lines)

    @mcp.resource("telecom://stats")
    def database_stats() -> str:
        """Statistiques générales de la base de données."""
        with db_session(read_only=True) as conn:
            tables = [r[0] for r in conn.execute("SHOW TABLES").fetchall()]
            counts = {}
            for table in tables:
                count = conn.execute(
                    f"SELECT count(*) FROM {table}"
                ).fetchone()[0]  # type: ignore[index]
                counts[table] = count

        lines = ["État de la base Observatoire Télécom:\n"]
        for table, count in counts.items():
            lines.append(f"  {table}: {count:,} lignes")
        return "\n".join(lines)
