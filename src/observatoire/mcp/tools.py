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
    def find_nearby_antennas(
        latitude: float,
        longitude: float,
        radius_km: float = 2.0,
        technology: str = "4G",
    ) -> str:
        """Trouve les antennes proches d'un point GPS.

        Utile pour savoir quels opérateurs couvrent un lieu précis.

        Args:
            latitude: Latitude du point (ex: 43.6047 pour Toulouse)
            longitude: Longitude du point (ex: 1.4442 pour Toulouse)
            radius_km: Rayon de recherche en kilomètres (défaut: 2km)
            technology: Technologie réseau (2G, 3G, 4G, 5G)
        """
        from observatoire.db.queries import get_nearby_antennas

        with db_session(read_only=True) as conn:
            results = get_nearby_antennas(
                conn, latitude, longitude, radius_km, technology, limit=20
            )

        if not results:
            return f"Aucune antenne {technology} dans un rayon de {radius_km}km."

        lines = [
            f"Antennes {technology} dans un rayon de {radius_km}km "
            f"de ({latitude:.4f}, {longitude:.4f}):\n"
        ]
        for r in results:
            lines.append(
                f"  {r['operator']} — {r['distance_km']}km "
                f"(commune {r['commune_code']}, dept {r['department_code']})"
            )
        lines.append(f"\n  Total: {len(results)} antennes")

        return "\n".join(lines)

    @mcp.tool()
    def analyze_route_coverage(
        line_id: str,
        technology: str = "4G",
        buffer_km: float = 2.0,
    ) -> str:
        """Analyse la couverture reseau le long d'une ligne ferroviaire SNCF.

        Calcule le pourcentage de couverture par operateur en creant un buffer
        autour du trace et en l'intersectant avec les polygones ARCEP.

        Args:
            line_id: Identifiant de la ligne RFN (ex: "001000")
            technology: Technologie reseau (2G, 3G, 4G)
            buffer_km: Rayon du buffer autour du trace en km (defaut: 2km)
        """
        from observatoire.db.queries import get_route_coverage

        with db_session(read_only=True) as conn:
            results = get_route_coverage(conn, line_id, technology, buffer_km)

        if not results:
            return (
                f"Aucune donnee de couverture {technology} trouvee "
                f"pour la ligne {line_id} (buffer {buffer_km}km)."
            )

        first = results[0]
        total_km = first.get("total_length_km", 0)
        lines = [
            f"Couverture {technology} le long de la ligne {line_id} "
            f"({total_km:.0f} km, buffer {buffer_km}km):\n"
        ]

        for i, r in enumerate(results, 1):
            name = r.get("operator_name") or r["operator"]
            pct = r["coverage_pct"]
            covered = r["covered_length_km"]
            lines.append(f"  {i}. {name}: {pct:.1f}% ({covered:.0f} km couverts)")

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
