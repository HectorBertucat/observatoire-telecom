/* Gestion des graphiques Chart.js */

const CHART_OPERATOR_COLORS = {
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

/**
 * Met à jour le graphique de géométries par opérateur.
 */
function updateCoverageChart(data) {
    const ctx = document.getElementById("coverage-chart").getContext("2d");

    if (coverageChart) coverageChart.destroy();

    const labels = data.map((d) => OPERATOR_NAMES[d.operator] || d.operator_name || d.operator);
    const values = data.map((d) => d.geometry_count);
    const colors = data.map((d) => CHART_OPERATOR_COLORS[d.operator] || "#999");

    coverageChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Polygones de couverture",
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
                y: {
                    beginAtZero: true,
                    title: { display: true, text: "Nombre de polygones" },
                },
            },
            plugins: { legend: { display: false } },
        },
    });
}
