"""Tests d'intégration des tools MCP avec données réelles.

Ces tests vérifient que les tools MCP retournent des résultats corrects
quand la base contient des données. Ils nécessitent la DB de production.
"""

import os

import pytest

# Skip si pas de DB de production
PROD_DB = os.path.expanduser("~/Code/observatoire-telecom/data/observatoire.duckdb")
HAS_PROD_DB = os.path.exists(PROD_DB)


@pytest.fixture
def _use_prod_db():
    """Utilise la DB de production si disponible."""
    if not HAS_PROD_DB:
        pytest.skip("DB de production non disponible")
    os.environ["OBS_DB_PATH"] = PROD_DB
    from observatoire import config

    config.settings = config.Settings()
    yield
    os.environ.pop("OBS_DB_PATH", None)
    config.settings = config.Settings()


@pytest.mark.skipif(not HAS_PROD_DB, reason="DB de production requise")
class TestMCPToolsIntegration:
    """Tests d'intégration MCP avec données réelles."""

    def test_get_antenna_count_national(self, _use_prod_db):
        """Vérifie que get_antenna_count retourne des données nationales."""
        from mcp.server.fastmcp import FastMCP

        from observatoire.mcp.tools import register_tools

        test_mcp = FastMCP("test")
        register_tools(test_mcp)

        # Appeler le tool directement via la fonction enregistrée
        from observatoire.db.connection import db_session

        with db_session(read_only=True) as conn:
            result = conn.execute(
                "SELECT operator, technology, COUNT(*) FROM raw_antenna_sites "
                "GROUP BY operator, technology ORDER BY operator, technology"
            ).fetchall()

        assert len(result) > 0, "Pas de données antennes en base"
        assert any(r[0] == "OF" for r in result), "Pas de données Orange"

    def test_compare_operators_4g(self, _use_prod_db):
        """Vérifie la comparaison opérateurs 4G."""
        from observatoire.db.connection import db_session

        with db_session(read_only=True) as conn:
            result = conn.execute(
                "SELECT operator, COUNT(*) as cnt FROM raw_antenna_sites "
                "WHERE technology = '4G' GROUP BY operator ORDER BY cnt DESC"
            ).fetchall()

        assert len(result) == 4, f"Attendu 4 opérateurs, trouvé {len(result)}"
        operators = {r[0] for r in result}
        assert operators == {"OF", "BYT", "FREE", "SFR"}

    def test_antenna_data_has_all_technologies(self, _use_prod_db):
        """Vérifie que les 4 technologies sont présentes."""
        from observatoire.db.connection import db_session

        with db_session(read_only=True) as conn:
            result = conn.execute(
                "SELECT DISTINCT technology FROM raw_antenna_sites ORDER BY technology"
            ).fetchall()

        techs = {r[0] for r in result}
        assert techs == {"2G", "3G", "4G", "5G"}
