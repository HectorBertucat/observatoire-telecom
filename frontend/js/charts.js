/* Gestion des graphiques Chart.js */

const OPERATOR_COLORS = {
    OF: "#FF6600",
    SFR: "#E4002B",
    BYT: "#003DA5",
    FREE: "#CD1719",
};

const OPERATOR_NAMES = {
    OF: "Orange",
    SFR: "SFR",
    BYT: "Bouygues",
    FREE: "Free",
};

let coverageChart = null;
let antennasChart = null;

/**
 * Met à jour le graphique de couverture par opérateur.
 */
function updateCoverageChart(data) {
    const ctx = document.getElementById("coverage-chart").getContext("2d");

    if (coverageChart) coverageChart.destroy();

    const labels = data.map((d) => OPERATOR_NAMES[d.operator] || d.operator);
    const values = data.map((d) => d.avg_coverage);
    const colors = data.map((d) => OPERATOR_COLORS[d.operator] || "#999");

    coverageChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Couverture moyenne (%)",
                    data: values,
                    backgroundColor: colors,
                    borderRadius: 4,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, max: 100, title: { display: true, text: "%" } },
            },
            plugins: { legend: { display: false } },
        },
    });
}

/**
 * Met à jour le graphique du nombre d'antennes.
 */
function updateAntennasChart(data) {
    const ctx = document.getElementById("antennas-chart").getContext("2d");

    if (antennasChart) antennasChart.destroy();

    const labels = data.map((d) => OPERATOR_NAMES[d.operator] || d.operator);
    const values = data.map((d) => d.total_antennas);
    const colors = data.map((d) => OPERATOR_COLORS[d.operator] || "#999");

    antennasChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Nombre d'antennes",
                    data: values,
                    backgroundColor: colors,
                    borderRadius: 4,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, title: { display: true, text: "Antennes" } },
            },
            plugins: { legend: { display: false } },
        },
    });
}
