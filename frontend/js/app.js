/* App logic — dark dashboard */

const API_BASE = "/api/v1";

const APP_OPERATORS = {
    OF: { name: "Orange", color: "#f97316" },
    BYT: { name: "Bouygues Telecom", color: "#3b82f6" },
    FREE: { name: "Free Mobile", color: "#ec4899" },
    SFR: { name: "SFR", color: "#ef4444" },
};

/* === INIT === */
document.addEventListener("DOMContentLoaded", async () => {
    buildOperatorToggles();
    await Promise.all([loadDepartments(), loadAllStats()]);

    const input = document.getElementById("commune-input");
    if (input) input.addEventListener("keypress", (e) => { if (e.key === "Enter") searchCommune(); });
});

/* === OPERATOR TOGGLES === */
function buildOperatorToggles() {
    const container = document.getElementById("operator-toggles");
    if (!container) return;

    for (const [op, info] of Object.entries(APP_OPERATORS)) {
        const label = document.createElement("label");
        label.className = "operator-toggle";
        label.dataset.op = op;

        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.checked = true;
        cb.addEventListener("change", () => {
            toggleOperator(op, cb.checked);
            // If only one operator checked, highlight it
            const checked = document.querySelectorAll("#operator-toggles input:checked");
            if (checked.length === 1) {
                setOperatorHighlight(checked[0].closest(".operator-toggle").dataset.op);
            } else {
                setOperatorHighlight("all");
            }
        });

        const dot = document.createElement("span");
        dot.className = "operator-dot";
        dot.style.backgroundColor = info.color;

        const name = document.createElement("span");
        name.className = "operator-name";
        name.textContent = info.name;

        const count = document.createElement("span");
        count.className = "operator-count";
        count.id = `op-count-${op}`;

        label.appendChild(cb);
        label.appendChild(dot);
        label.appendChild(name);
        label.appendChild(count);
        container.appendChild(label);
    }
}

/* === TECHNOLOGY FILTER === */
function filterTechnology() {
    const tech = document.getElementById("tech-select").value;
    // Update map coverage filter via map.js function
    if (typeof window.filterTechnology === "function") {
        // Already handled by map.js
    }
    // Filter the map
    filterTechnologyOnMap(tech);
}

function filterTechnologyOnMap(tech) {
    if (typeof map === "undefined") return;
    for (const op of Object.keys(APP_OPERATORS)) {
        if (tech === "all") {
            map.setFilter(`coverage-fill-${op}`, ["==", ["get", "operator"], op]);
            map.setFilter(`coverage-line-${op}`, ["==", ["get", "operator"], op]);
        } else {
            map.setFilter(`coverage-fill-${op}`, [
                "all",
                ["==", ["get", "operator"], op],
                ["==", ["get", "technology"], tech],
            ]);
            map.setFilter(`coverage-line-${op}`, [
                "all",
                ["==", ["get", "operator"], op],
                ["==", ["get", "technology"], tech],
            ]);
        }
    }
}

/* === STATS === */
async function loadAllStats(deptCode) {
    await Promise.all([
        loadAntennaStats(deptCode),
        loadTopCommunes(deptCode),
    ]);
}

async function loadAntennaStats(deptCode) {
    try {
        const url = deptCode
            ? `${API_BASE}/antennas/department/${deptCode}`
            : `${API_BASE}/stats/antennas`;
        const response = await fetch(url);
        const data = await response.json();

        if (data.length > 0) {
            updateAntennasChart(data);
            updatePanelStats(data, deptCode);
        }
    } catch (error) {
        console.error("Stats error:", error);
    }
}

async function loadTopCommunes(deptCode) {
    try {
        const params = new URLSearchParams({ limit: "10" });
        if (deptCode) params.set("department", deptCode);
        const response = await fetch(`${API_BASE}/stats/top-communes?${params}`);
        const data = await response.json();
        updateTopCommunesChart(data, deptCode);
    } catch (error) {
        console.error("Top communes error:", error);
    }
}

function updatePanelStats(data, deptCode) {
    const container = document.getElementById("panel-stats");
    if (!container) return;
    while (container.firstChild) container.removeChild(container.firstChild);

    const total = data.reduce((s, d) => s + d.site_count, 0);
    const t4g = data.filter((d) => d.technology === "4G").reduce((s, d) => s + d.site_count, 0);
    const t5g = data.filter((d) => d.technology === "5G").reduce((s, d) => s + d.site_count, 0);
    const t3g = data.filter((d) => d.technology === "3G").reduce((s, d) => s + d.site_count, 0);
    const t2g = data.filter((d) => d.technology === "2G").reduce((s, d) => s + d.site_count, 0);

    const stats = [
        ["Total sites", total.toLocaleString("fr-FR")],
        ["2G GSM", t2g.toLocaleString("fr-FR")],
        ["3G UMTS", t3g.toLocaleString("fr-FR")],
        ["4G LTE", t4g.toLocaleString("fr-FR")],
        ["5G NR", t5g.toLocaleString("fr-FR")],
    ];

    stats.forEach(([label, value]) => {
        const row = document.createElement("div");
        row.className = "stat-mini";

        const labelEl = document.createElement("span");
        labelEl.className = "stat-mini-label";
        labelEl.textContent = label;

        const valueEl = document.createElement("span");
        valueEl.className = "stat-mini-value";
        valueEl.textContent = value;

        row.appendChild(labelEl);
        row.appendChild(valueEl);
        container.appendChild(row);
    });

    // Operator counts in toggles
    for (const op of Object.keys(APP_OPERATORS)) {
        const countEl = document.getElementById(`op-count-${op}`);
        if (countEl) {
            const opTotal = data.filter((d) => d.operator === op).reduce((s, d) => s + d.site_count, 0);
            countEl.textContent = opTotal.toLocaleString("fr-FR");
        }
    }
}

/* === DEPARTMENTS === */
async function loadDepartments() {
    try {
        const response = await fetch(`${API_BASE}/stats/departments`);
        const departments = await response.json();
        const select = document.getElementById("dept-select");
        departments.forEach((dept) => {
            const option = document.createElement("option");
            option.value = dept.code;
            option.textContent = `${dept.code} — ${dept.name}`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error("Departments error:", error);
    }
}

function selectDepartment() {
    const code = document.getElementById("dept-select").value;
    if (!code) {
        map.flyTo({ center: [2.888, 46.603], zoom: 5.5, duration: 1 });
        loadAllStats();
        return;
    }
    loadAllStats(code);
}

/* === COMMUNE SEARCH === */
async function searchCommune() {
    const code = document.getElementById("commune-input").value.trim();
    if (!code || code.length < 4) return;

    try {
        const response = await fetch(`${API_BASE}/antennas/commune/${code}`);
        const data = await response.json();
        if (data.total === 0) { alert(`Aucune antenne pour la commune ${code}.`); return; }
        map.flyTo({ center: [data.center.lon, data.center.lat], zoom: 13, duration: 1.5 });
    } catch (error) {
        console.error("Commune error:", error);
    }
}

/* === ACTIONS === */
function resetView() {
    map.flyTo({ center: [2.888, 46.603], zoom: 5.5, duration: 1 });
    document.getElementById("dept-select").value = "";
    loadAllStats();
}

function exportCSV() {
    const dept = document.getElementById("dept-select").value;
    const params = new URLSearchParams();
    if (dept) params.set("department", dept);
    window.open(`${API_BASE}/antennas/export.csv?${params.toString()}`, "_blank");
}
