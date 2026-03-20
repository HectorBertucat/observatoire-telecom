/* Gestion des graphiques Chart.js */

const CHART_OPERATOR_COLORS = {
    OF: "#FF6600",
    SFR: "#E4002B",
    BYT: "#003DA5",
    FREE: "#CD1719",
};

const CHART_OPERATOR_NAMES = {
    OF: "Orange",
    SFR: "SFR",
    BYT: "Bouygues",
    FREE: "Free",
};

const TECH_COLORS = {
    "2G": "#94a3b8",
    "3G": "#60a5fa",
    "4G": "#34d399",
    "5G": "#a78bfa",
};

let antennasChart = null;

/**
 * Met à jour le graphique d'antennes par opérateur et technologie.
 */
function updateAntennasChart(data) {
    const ctx = document.getElementById("antennas-chart").getContext("2d");
    if (antennasChart) antennasChart.destroy();

    // Grouper par opérateur
    const operators = [...new Set(data.map((d) => d.operator))];
    const technologies = ["2G", "3G", "4G", "5G"];

    const datasets = technologies.map((tech) => ({
        label: tech,
        data: operators.map((op) => {
            const entry = data.find((d) => d.operator === op && d.technology === tech);
            return entry ? entry.site_count : 0;
        }),
        backgroundColor: TECH_COLORS[tech],
        borderRadius: 3,
    }));

    antennasChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: operators.map((op) => CHART_OPERATOR_NAMES[op] || op),
            datasets: datasets,
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { stacked: true },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    title: { display: true, text: "Nombre de sites" },
                    ticks: {
                        callback: (v) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v,
                    },
                },
            },
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { boxWidth: 12, padding: 8, font: { size: 11 } },
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: ${ctx.raw.toLocaleString("fr-FR")} sites`,
                    },
                },
            },
        },
    });
}
