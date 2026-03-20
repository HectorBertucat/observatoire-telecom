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
 * Recentre la vue sur la France métropolitaine.
 */
function resetView() {
    map.flyTo({ center: [2.888, 46.603], zoom: 5.5, duration: 1 });
}

/**
 * Crée une carte de statistique via DOM API.
 */
function createStatCard(label, value, subtitle) {
    const card = document.createElement("div");
    card.className = "stat-card";

    const valueEl = document.createElement("div");
    valueEl.className = "value";
    valueEl.textContent = typeof value === "number" ? value.toLocaleString("fr-FR") : value;

    const labelEl = document.createElement("div");
    labelEl.className = "label";
    labelEl.textContent = label;

    card.appendChild(valueEl);
    card.appendChild(labelEl);

    if (subtitle) {
        const subEl = document.createElement("div");
        subEl.className = "label";
        subEl.style.fontSize = "0.7rem";
        subEl.style.marginTop = "2px";
        subEl.textContent = subtitle;
        card.appendChild(subEl);
    }

    return card;
}

/**
 * Met à jour la grille de statistiques avec des données enrichies.
 */
async function updateStats() {
    const grid = document.getElementById("stats-grid");
    while (grid.firstChild) grid.removeChild(grid.firstChild);

    try {
        // Charger stats tables + antennes en parallèle
        const [tablesRes, antennasRes] = await Promise.all([
            fetch(`${API_BASE}/stats/tables`),
            fetch(`${API_BASE}/stats/antennas`),
        ]);

        const tables = await tablesRes.json();
        const antennas = await antennasRes.json();

        // Calculs
        const totalAntennas = antennas.reduce((sum, a) => sum + a.site_count, 0);
        const total4G = antennas
            .filter((a) => a.technology === "4G")
            .reduce((sum, a) => sum + a.site_count, 0);
        const total5G = antennas
            .filter((a) => a.technology === "5G")
            .reduce((sum, a) => sum + a.site_count, 0);
        const coveragePolygons = tables["raw_coverage"] || 0;
        const operators = new Set(antennas.map((a) => a.operator)).size;

        grid.appendChild(createStatCard("Sites d'antennes", totalAntennas, "Toutes technologies"));
        grid.appendChild(createStatCard("Sites 4G", total4G, "LTE"));
        grid.appendChild(createStatCard("Sites 5G", total5G, "NR"));
        grid.appendChild(createStatCard("Opérateurs", operators, "Métropole"));
        grid.appendChild(createStatCard("Polygones couverture", coveragePolygons, "ARCEP 4G"));

        // Mettre à jour le graphique
        updateAntennasChart(antennas);
    } catch (error) {
        console.error("Erreur chargement stats:", error);
        const placeholder = document.createElement("p");
        placeholder.className = "placeholder";
        placeholder.textContent = "Erreur de chargement.";
        grid.appendChild(placeholder);
    }
}

/**
 * Recherche une commune par code INSEE et zoome dessus.
 */
async function searchCommune() {
    const code = document.getElementById("commune-input").value.trim();
    if (!code || code.length < 4) return;

    try {
        const response = await fetch(`${API_BASE}/antennas/commune/${code}`);
        const data = await response.json();

        if (data.total === 0) {
            alert(`Aucune antenne trouvée pour la commune ${code}.`);
            return;
        }

        // Zoomer sur la commune
        map.flyTo({
            center: [data.center.lon, data.center.lat],
            zoom: 13,
            duration: 1.5,
        });

        // Afficher un résumé dans la console et via popup
        const summary = data.operators
            .map((o) => `${o.operator} ${o.technology}: ${o.count}`)
            .join(", ");
        console.log(`Commune ${code}: ${data.total} antennes — ${summary}`);
    } catch (error) {
        console.error("Erreur recherche commune:", error);
    }
}

// Enter key sur l'input commune
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("commune-input");
    if (input) {
        input.addEventListener("keypress", (e) => {
            if (e.key === "Enter") searchCommune();
        });
    }
});

/**
 * Charge la liste des départements dans le sélecteur.
 */
async function loadDepartments() {
    try {
        const response = await fetch(`${API_BASE}/stats/departments`);
        const departments = await response.json();
        const select = document.getElementById("dept-select");

        departments.forEach((dept) => {
            const option = document.createElement("option");
            option.value = dept.code;
            option.textContent = `${dept.code} - ${dept.name} (${dept.antenna_count.toLocaleString("fr-FR")})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error("Erreur chargement départements:", error);
    }
}

/**
 * Sélectionne un département : zoom + stats locales.
 */
async function selectDepartment() {
    const code = document.getElementById("dept-select").value;

    if (!code) {
        // Retour au national
        map.flyTo({ center: [2.888, 46.603], zoom: 5.5, duration: 1 });
        updateStats();
        return;
    }

    // Charger les stats du département
    try {
        const response = await fetch(`${API_BASE}/antennas/department/${code}`);
        const data = await response.json();

        if (data.length > 0) {
            updateAntennasChart(data);

            // Mettre à jour les stats cards
            const grid = document.getElementById("stats-grid");
            while (grid.firstChild) grid.removeChild(grid.firstChild);

            const total = data.reduce((s, d) => s + d.site_count, 0);
            const t4g = data.filter((d) => d.technology === "4G").reduce((s, d) => s + d.site_count, 0);
            const t5g = data.filter((d) => d.technology === "5G").reduce((s, d) => s + d.site_count, 0);
            const ops = new Set(data.map((d) => d.operator)).size;

            grid.appendChild(createStatCard("Sites dept " + code, total, "Toutes technologies"));
            grid.appendChild(createStatCard("Sites 4G", t4g, "LTE"));
            grid.appendChild(createStatCard("Sites 5G", t5g, "NR"));
            grid.appendChild(createStatCard("Opérateurs", ops, "Dans ce département"));
        }
    } catch (error) {
        console.error("Erreur stats département:", error);
    }
}

// Chargement initial
document.addEventListener("DOMContentLoaded", () => {
    loadDepartments();
    updateStats();
});
