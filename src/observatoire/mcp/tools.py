"""Tools MCP pour interroger les données télécom."""

from mcp.server.fastmcp import FastMCP

from observatoire.db.connection import db_session


def register_tools(mcp: FastMCP) -> None:
    """Enregistre les tools MCP auprès du serveur."""

    @mcp.tool()
    def get_antenna_count(
        commune_code: str | None = None,
        technology: str | None = None,
    ) -> str:
        """Compte les antennes par opérateur pour une commune ou au niveau national.

        Args:
            commune_code: Code INSEE de la commune (ex: 31555 pour Toulouse). Optionnel.
            technology: Technologie réseau (2G, 3G, 4G, 5G). Optionnel.
        """
        with db_session(read_only=True) as conn:
            conditions = []
            params: list[str] = []

            if commune_code:
                conditions.append("commune_code = ?")
                params.append(commune_code)
            if technology:
                conditions.append("technology = ?")
                params.append(technology)

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            result = conn.execute(
                f"""
                SELECT operator, technology, COUNT(*) AS cnt
                FROM raw_antenna_sites
                {where}
                GROUP BY operator, technology
                ORDER BY operator, technology
                """,
                params,
            ).fetchall()

        if not result:
            zone = f"commune {commune_code}" if commune_code else "France"
            return f"Aucune antenne trouvée pour {zone}."

        zone = f"Commune {commune_code}" if commune_code else "France entière"
        tech_label = f" ({technology})" if technology else ""
        lines = [f"Antennes{tech_label} — {zone}:\n"]

        total = 0
        for row in result:
            lines.append(f"  {row[0]} ({row[1]}): {row[2]:,} sites")
            total += row[2]
        lines.append(f"\n  Total: {total:,} sites")

        return "\n".join(lines)

    @mcp.tool()
    def compare_operators(technology: str = "4G") -> str:
        """Compare le nombre d'antennes de tous les opérateurs au niveau national.

        Utile pour identifier quel opérateur a le plus de sites déployés.

        Args:
            technology: Technologie réseau (2G, 3G, 4G, 5G)
        """
        with db_session(read_only=True) as conn:
            result = conn.execute(
                """
                SELECT
                    a.operator,
                    ro.name AS operator_name,
                    COUNT(*) AS site_count
                FROM raw_antenna_sites a
                LEFT JOIN ref_operators ro ON a.operator = ro.code
                WHERE a.technology = ?
                GROUP BY a.operator, ro.name
                ORDER BY site_count DESC
                """,
                [technology],
            ).fetchall()

        if not result:
            return f"Aucune donnée {technology}."

        lines = [f"Classement {technology} — Sites d'antennes en France:\n"]
        for i, row in enumerate(result, 1):
            name = row[1] or row[0]
            lines.append(f"  {i}. {name}: {row[2]:,} sites")

        if len(result) >= 2:
            gap = result[0][2] - result[-1][2]
            lines.append(f"\n  Ecart 1er-dernier: {gap:,} sites")

        return "\n".join(lines)

    @mcp.tool()
    def get_coverage_summary() -> str:
        """Retourne un résumé des données de couverture disponibles.

        Indique les opérateurs, technologies et volumes de données en base.
        """
        with db_session(read_only=True) as conn:
            # Stats couverture
            coverage = conn.execute("""
                SELECT operator_code, technology, quarter, COUNT(*) as cnt
                FROM raw_coverage
                GROUP BY operator_code, technology, quarter
                ORDER BY operator_code
            """).fetchall()

            # Stats antennes
            antennas = conn.execute("""
                SELECT operator, technology, COUNT(*) as cnt
                FROM raw_antenna_sites
                GROUP BY operator, technology
                ORDER BY operator, technology
            """).fetchall()

            total_antennas = conn.execute("SELECT COUNT(*) FROM raw_antenna_sites").fetchone()[0]  # type: ignore[index]

        lines = ["=== Observatoire Télécom France ===\n"]

        lines.append("Couverture théorique ARCEP:")
        for row in coverage:
            lines.append(f"  {row[0]} {row[1]} ({row[2]}): {row[3]} polygones")

        lines.append(f"\nSites d'antennes ANFR ({total_antennas:,} total):")
        for row in antennas:
            lines.append(f"  {row[0]} {row[1]}: {row[2]:,} sites")

        return "\n".join(lines)

    @mcp.tool()
    def search_antennas(
        commune_code: str,
        technology: str = "4G",
        limit: int = 20,
    ) -> str:
        """Recherche les antennes dans une commune donnée.

        Retourne la liste des sites avec coordonnées GPS.

        Args:
            commune_code: Code INSEE de la commune (ex: 31555)
            technology: Technologie réseau (2G, 3G, 4G, 5G)
            limit: Nombre max de résultats (1-50)
        """
        limit = min(limit, 50)

        with db_session(read_only=True) as conn:
            result = conn.execute(
                """
                SELECT id, operator, latitude, longitude, technology
                FROM raw_antenna_sites
                WHERE commune_code = ? AND technology = ?
                LIMIT ?
                """,
                [commune_code, technology, limit],
            ).fetchall()

        if not result:
            return f"Aucune antenne {technology} dans la commune {commune_code}."

        lines = [f"Antennes {technology} — Commune {commune_code} ({len(result)} sites):\n"]
        for row in result:
            lines.append(f"  [{row[1]}] Site {row[0]} — {row[3]:.5f}°E, {row[2]:.5f}°N")

        return "\n".join(lines)
