/* Logique principale du dashboard */

const API_BASE = "/api/v1";

/**
 * Charge les données au clic sur Afficher.
 */
async function loadData() {
    const operator = document.getElementById("operator-select").value;
    const technology = document.getElementById("tech-select").value;

    if (!operator) return;

    setLoading(true);
    clearCoverageLayers();

    await loadCoverageLayer(operator, technology);
    // Recentrer sur la France après chargement
    map.setView([46.603, 2.888], 6);

    await loadStats(technology);
    setLoading(false);
}

/**
 * Charge toutes les couvertures (tous opérateurs) sur la carte.
 */
async function loadAllOperators() {
    const technology = document.getElementById("tech-select").value;

    setLoading(true);
    clearCoverageLayers();

    const operators = ["OF", "BYT", "FREE", "SFR"];
    await Promise.all(operators.map((op) => loadCoverageLayer(op, technology)));

    map.setView([46.603, 2.888], 6);
    await loadStats(technology);
    setLoading(false);
}

/**
 * Affiche/masque l'indicateur de chargement.
 */
function setLoading(loading) {
    const buttons = document.querySelectorAll("nav button");
    buttons.forEach((btn) => {
        btn.disabled = loading;
        if (loading) {
            btn.style.opacity = "0.6";
        } else {
            btn.style.opacity = "1";
        }
    });
}

/**
 * Charge les stats de couverture.
 */
async function loadStats(technology) {
    try {
        const response = await fetch(`${API_BASE}/stats/coverage?technology=${technology}`);
        const data = await response.json();

        if (data.length > 0) {
            updateCoverageChart(data);
        }
    } catch (error) {
        console.error("Erreur chargement stats:", error);
    }
}

/**
 * Crée une carte de statistique via DOM API.
 */
function createStatCard(table, count) {
    const card = document.createElement("div");
    card.className = "stat-card";

    const valueEl = document.createElement("div");
    valueEl.className = "value";
    valueEl.textContent = count.toLocaleString("fr-FR");

    const labelEl = document.createElement("div");
    labelEl.className = "label";
    labelEl.textContent = table;

    card.appendChild(valueEl);
    card.appendChild(labelEl);
    return card;
}

/**
 * Met à jour la grille de statistiques.
 */
function updateStatsGrid(counts) {
    const grid = document.getElementById("stats-grid");

    while (grid.firstChild) {
        grid.removeChild(grid.firstChild);
    }

    const entries = Object.entries(counts);
    if (entries.length === 0) {
        const placeholder = document.createElement("p");
        placeholder.className = "placeholder";
        placeholder.textContent = "Aucune donnée disponible.";
        grid.appendChild(placeholder);
        return;
    }

    for (const [table, count] of entries) {
        grid.appendChild(createStatCard(table, count));
    }
}

// Chargement initial
document.addEventListener("DOMContentLoaded", async () => {
    try {
        const tablesRes = await fetch(`${API_BASE}/stats/tables`);
        const counts = await tablesRes.json();
        updateStatsGrid(counts);

        await loadStats("4G");
    } catch (error) {
        console.error("Erreur chargement initial:", error);
    }
});
