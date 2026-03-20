"""Tools MCP pour interroger les données télécom."""

from mcp.server.fastmcp import FastMCP

from observatoire.db.connection import db_session


def register_tools(mcp: FastMCP) -> None:
    """Enregistre les tools MCP auprès du serveur."""

    @mcp.tool()
    def get_coverage(commune_code: str, technology: str = "4G") -> str:
        """Retourne la couverture réseau mobile pour une commune donnée.

        Fournit le pourcentage de couverture par opérateur et par technologie.

        Args:
            commune_code: Code INSEE de la commune (ex: 31555 pour Toulouse)
            technology: Technologie réseau (2G, 3G, 4G, 5G)
        """
        with db_session(read_only=True) as conn:
            result = conn.execute(
                """
                SELECT operator_code, coverage_pct, antenna_count
                FROM mart_coverage_by_commune
                WHERE commune_code = ? AND technology = ?
                ORDER BY coverage_pct DESC
                """,
                [commune_code, technology],
            ).fetchall()

        if not result:
            return f"Aucune donnée de couverture {technology} pour la commune {commune_code}."

        lines = [f"Couverture {technology} — Commune {commune_code}:\n"]
        for row in result:
            lines.append(f"  {row[0]}: {row[1]:.1f}% ({row[2]} antennes)")

        return "\n".join(lines)

    @mcp.tool()
    def compare_operators(department_code: str, technology: str = "4G") -> str:
        """Compare la couverture de tous les opérateurs pour un département.

        Utile pour identifier quel opérateur couvre le mieux une zone.

        Args:
            department_code: Code département (ex: 31 pour Haute-Garonne)
            technology: Technologie réseau (2G, 3G, 4G, 5G)
        """
        with db_session(read_only=True) as conn:
            result = conn.execute(
                """
                SELECT
                    operator_code,
                    ROUND(AVG(coverage_pct), 1) AS avg_coverage,
                    SUM(antenna_count) AS total_antennas,
                    COUNT(DISTINCT commune_code) AS communes
                FROM mart_coverage_by_commune
                WHERE department_code = ? AND technology = ?
                GROUP BY operator_code
                ORDER BY avg_coverage DESC
                """,
                [department_code, technology],
            ).fetchall()

        if not result:
            return f"Aucune donnée {technology} pour le département {department_code}."

        lines = [f"Comparaison {technology} — Département {department_code}:\n"]
        for row in result:
            lines.append(
                f"  {row[0]}: {row[1]}% couverture moyenne, {row[2]} antennes, {row[3]} communes"
            )

        return "\n".join(lines)

    @mcp.tool()
    def get_antenna_density(department_code: str, operator: str | None = None) -> str:
        """Calcule la densité d'antennes pour une zone géographique.

        Args:
            department_code: Code département (ex: 31)
            operator: Code opérateur optionnel (BYT, FREE, OF, SFR). Tous si omis.
        """
        with db_session(read_only=True) as conn:
            params: list[str] = [department_code]
            operator_filter = ""
            if operator:
                operator_filter = "AND operator = ?"
                params.append(operator)

            result = conn.execute(
                f"""
                SELECT
                    operator,
                    technology,
                    COUNT(*) AS antenna_count
                FROM raw_antenna_sites
                WHERE department_code = ?
                  {operator_filter}
                GROUP BY operator, technology
                ORDER BY operator, technology
                """,
                params,
            ).fetchall()

        if not result:
            return f"Aucune donnée d'antennes pour le département {department_code}."

        lines = [f"Antennes — Département {department_code}:\n"]
        for row in result:
            lines.append(f"  {row[0]} ({row[1]}): {row[2]} antennes")

        return "\n".join(lines)
