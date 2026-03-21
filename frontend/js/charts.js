/* Charts — dark theme */

Chart.defaults.color = "#94a3b8";
Chart.defaults.borderColor = "rgba(255,255,255,0.06)";
Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Inter', sans-serif";

const CHART_COLORS = {
    OF: "#f97316",
    BYT: "#3b82f6",
    FREE: "#ec4899",
    SFR: "#ef4444",
};

const CHART_NAMES = {
    OF: "Orange",
    BYT: "Bouygues",
    FREE: "Free",
    SFR: "SFR",
};

const TECH_COLORS = {
    "2G": "#64748b",
    "3G": "#6366f1",
    "4G": "#10b981",
    "5G": "#a78bfa",
};

let antennasChart = null;
let techChart = null;

function updateAntennasChart(data) {
    const ctx = document.getElementById("antennas-chart");
    if (!ctx) return;
    if (antennasChart) antennasChart.destroy();

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
        borderSkipped: false,
    }));

    antennasChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: operators.map((op) => CHART_NAMES[op] || op),
            datasets,
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: "y",
            scales: {
                x: {
                    stacked: true,
                    grid: { color: "rgba(255,255,255,0.04)" },
                    ticks: { callback: (v) => (v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v) },
                },
                y: {
                    stacked: true,
                    grid: { display: false },
                },
            },
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { boxWidth: 10, padding: 12, font: { size: 11 } },
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) =>
                            `${ctx.dataset.label}: ${ctx.raw.toLocaleString("fr-FR")}`,
                    },
                },
            },
        },
    });

    // Update tech doughnut
    updateTechChart(data);
}

function updateTechChart(data) {
    const ctx = document.getElementById("tech-chart");
    if (!ctx) return;
    if (techChart) techChart.destroy();

    const techTotals = {};
    data.forEach((d) => {
        techTotals[d.technology] = (techTotals[d.technology] || 0) + d.site_count;
    });

    const techs = Object.keys(techTotals).sort();
    const values = techs.map((t) => techTotals[t]);
    const colors = techs.map((t) => TECH_COLORS[t] || "#666");

    techChart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: techs,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: "rgba(15, 23, 41, 0.8)",
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "55%",
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { boxWidth: 10, padding: 10, font: { size: 11 } },
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = ((ctx.raw / total) * 100).toFixed(1);
                            return `${ctx.label}: ${ctx.raw.toLocaleString("fr-FR")} (${pct}%)`;
                        },
                    },
                },
            },
        },
    });
}
