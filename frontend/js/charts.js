/* Charts — dark theme, 3 panels */

Chart.defaults.color = "#94a3b8";
Chart.defaults.borderColor = "rgba(255,255,255,0.04)";
Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Inter', sans-serif";
Chart.defaults.font.size = 11;

const CHART_COLORS = {
    OF: "#f97316", BYT: "#3b82f6", FREE: "#ec4899", SFR: "#ef4444",
};
const CHART_NAMES = {
    OF: "Orange", BYT: "Bouygues", FREE: "Free", SFR: "SFR",
};
const TECH_COLORS = {
    "2G": "#64748b", "3G": "#6366f1", "4G": "#10b981", "5G": "#a78bfa",
};

let antennasChart = null;
let techChart = null;
let topCommunesChart = null;
let routeCoverageChart = null;

/* === Horizontal stacked bar: antennes par opérateur × techno === */
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
        borderRadius: 2,
        borderSkipped: false,
    }));

    antennasChart = new Chart(ctx, {
        type: "bar",
        data: { labels: operators.map((op) => CHART_NAMES[op] || op), datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: "y",
            scales: {
                x: {
                    stacked: true,
                    grid: { color: "rgba(255,255,255,0.03)" },
                    ticks: { callback: (v) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v },
                },
                y: { stacked: true, grid: { display: false } },
            },
            plugins: {
                legend: { position: "bottom", labels: { boxWidth: 8, padding: 10 } },
                tooltip: {
                    callbacks: {
                        label: (c) => `${c.dataset.label}: ${c.raw.toLocaleString("fr-FR")} sites`,
                    },
                },
            },
        },
    });

    updateTechChart(data);
}

/* === Doughnut: répartition par techno === */
function updateTechChart(data) {
    const ctx = document.getElementById("tech-chart");
    if (!ctx) return;
    if (techChart) techChart.destroy();

    const totals = {};
    data.forEach((d) => { totals[d.technology] = (totals[d.technology] || 0) + d.site_count; });
    const techs = Object.keys(totals).sort();

    techChart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: techs,
            datasets: [{
                data: techs.map((t) => totals[t]),
                backgroundColor: techs.map((t) => TECH_COLORS[t] || "#666"),
                borderColor: "#0f1729",
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "50%",
            plugins: {
                legend: { position: "bottom", labels: { boxWidth: 8, padding: 8 } },
                tooltip: {
                    callbacks: {
                        label: (c) => {
                            const total = c.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = ((c.raw / total) * 100).toFixed(1);
                            return `${c.label}: ${c.raw.toLocaleString("fr-FR")} (${pct}%)`;
                        },
                    },
                },
            },
        },
    });
}

/* === Top communes horizontal bar === */
function updateTopCommunesChart(communes, deptCode) {
    const ctx = document.getElementById("top-communes-chart");
    if (!ctx) return;
    if (topCommunesChart) topCommunesChart.destroy();

    const titleEl = document.getElementById("top-communes-title");
    if (titleEl) {
        titleEl.textContent = deptCode
            ? `Top 10 communes — dept ${deptCode}`
            : "Top 10 communes nationales";
    }

    const labels = communes.map((c) =>
        c.commune_name ? `${c.commune_name} (${c.department_code})` : c.commune_code
    );
    const values = communes.map((c) => c.total);

    topCommunesChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: "rgba(59, 130, 246, 0.6)",
                borderRadius: 2,
                borderSkipped: false,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: "y",
            scales: {
                x: {
                    grid: { color: "rgba(255,255,255,0.03)" },
                    ticks: { callback: (v) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v },
                },
                y: {
                    grid: { display: false },
                    ticks: { font: { size: 10 } },
                },
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (c) => `${c.raw.toLocaleString("fr-FR")} antennes`,
                    },
                },
            },
        },
    });
}

/* === Route coverage horizontal bar === */
function updateRouteCoverageChart(data) {
    const card = document.getElementById("route-chart-card");
    const ctx = document.getElementById("route-coverage-chart");
    if (!ctx) return;
    if (routeCoverageChart) routeCoverageChart.destroy();

    if (!data || data.length === 0) {
        if (card) card.style.display = "none";
        return;
    }

    if (card) card.style.display = "block";

    const labels = data.map((d) => CHART_NAMES[d.operator] || d.operator_name || d.operator);
    const values = data.map((d) => d.coverage_pct);
    const colors = data.map((d) => CHART_COLORS[d.operator] || "#666");

    routeCoverageChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderRadius: 2,
                borderSkipped: false,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: "y",
            scales: {
                x: {
                    min: 0,
                    max: 100,
                    grid: { color: "rgba(255,255,255,0.03)" },
                    ticks: { callback: (v) => `${v}%` },
                },
                y: {
                    grid: { display: false },
                    ticks: { font: { size: 11 } },
                },
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (c) => {
                            const d = data[c.dataIndex];
                            return `${c.raw}% (${d.covered_length_km} km / ${d.total_length_km} km)`;
                        },
                    },
                },
            },
        },
    });
}
