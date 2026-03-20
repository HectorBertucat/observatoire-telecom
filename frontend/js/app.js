/* Logique principale du dashboard */

const API_BASE = "/api/v1";

/**
 * Applique le filtre opérateur sur la carte.
 */
function applyFilter() {
    const operator = document.getElementById("operator-select").value;
    filterByOperator(operator);
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
