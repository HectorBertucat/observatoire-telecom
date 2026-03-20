"""Requêtes SQL métier réutilisables."""

import duckdb


def get_commune_coverage(
    conn: duckdb.DuckDBPyConnection,
    commune_code: str,
    technology: str = "4G",
) -> list[dict]:
    """Retourne la couverture d'une commune par opérateur."""
    result = conn.execute(
        """
        SELECT
            commune_code,
            commune_name,
            operator_code AS operator,
            technology,
            coverage_pct,
            antenna_count,
            total_population AS population
        FROM mart_coverage_by_commune
        WHERE commune_code = ?
          AND technology = ?
        ORDER BY coverage_pct DESC
        """,
        [commune_code, technology],
    ).fetchall()

    columns = [
        "commune_code",
        "commune_name",
        "operator",
        "technology",
        "coverage_pct",
        "antenna_count",
        "population",
    ]
    return [dict(zip(columns, row, strict=True)) for row in result]


def get_department_stats(
    conn: duckdb.DuckDBPyConnection,
    department_code: str,
    technology: str = "4G",
) -> list[dict]:
    """Retourne les statistiques de couverture par opérateur pour un département."""
    result = conn.execute(
        """
        SELECT
            operator_code AS operator,
            technology,
            ROUND(AVG(coverage_pct), 1) AS avg_coverage,
            SUM(antenna_count) AS total_antennas,
            COUNT(DISTINCT commune_code) AS commune_count
        FROM mart_coverage_by_commune
        WHERE department_code = ?
          AND technology = ?
        GROUP BY operator_code, technology
        ORDER BY avg_coverage DESC
        """,
        [department_code, technology],
    ).fetchall()

    columns = ["operator", "technology", "avg_coverage", "total_antennas", "commune_count"]
    return [dict(zip(columns, row, strict=True)) for row in result]


def get_table_counts(conn: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Retourne le nombre de lignes par table."""
    tables = [row[0] for row in conn.execute("SHOW TABLES").fetchall()]
    counts: dict[str, int] = {}
    for table in tables:
        count = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]  # type: ignore[index]
        counts[table] = count
    return counts
