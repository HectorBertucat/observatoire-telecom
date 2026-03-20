/* Logique principale du dashboard */

const API_BASE = "/api/v1";

/**
 * Charge les données pour le département sélectionné.
 */
async function loadData() {
    const department = document.getElementById("department-select").value;
    const technology = document.getElementById("tech-select").value;

    if (!department) {
        alert("Veuillez sélectionner un département.");
        return;
    }

    // Mettre à jour la carte
    updateMap(department);

    // Charger les stats département
    try {
        const response = await fetch(
            `${API_BASE}/stats/department/${department}?technology=${technology}`
        );
        const data = await response.json();

        if (data.length > 0) {
            updateCoverageChart(data);
            updateAntennasChart(data);
        }
    } catch (error) {
        console.error("Erreur chargement stats:", error);
    }

    // Charger les comptages de tables
    try {
        const response = await fetch(`${API_BASE}/stats/tables`);
        const counts = await response.json();
        updateStatsGrid(counts);
    } catch (error) {
        console.error("Erreur chargement tables:", error);
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

    // Vider le contenu existant
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

// Charger les stats au démarrage
document.addEventListener("DOMContentLoaded", async () => {
    try {
        const response = await fetch(`${API_BASE}/stats/tables`);
        const counts = await response.json();
        updateStatsGrid(counts);
    } catch (error) {
        console.error("Erreur chargement initial:", error);
    }
});
