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

/* === TRAJET FERROVIAIRE === */

// Etat des deux gares selectionnees
const _route = {
    departure: null, // { station_name, line_codes, latitude, longitude, ... }
    arrival: null,
    selectedLineId: null,
};

document.addEventListener("DOMContentLoaded", () => {
    // Initialiser les deux autocompletes
    document.querySelectorAll(".autocomplete-wrapper").forEach((wrapper) => {
        const role = wrapper.dataset.role; // "departure" ou "arrival"
        if (!role) return;
        initStationAutocomplete(wrapper, role);
    });

    // Fermer tous les dropdowns si on clique ailleurs
    document.addEventListener("click", (e) => {
        if (!e.target.closest(".autocomplete-wrapper")) {
            document.querySelectorAll(".autocomplete-dropdown").forEach((d) => {
                d.classList.remove("visible");
            });
        }
    });
});

function initStationAutocomplete(wrapper, role) {
    const input = wrapper.querySelector(".station-input");
    const dropdown = wrapper.querySelector(".autocomplete-dropdown");
    let timeout = null;
    let activeIdx = -1;

    input.addEventListener("input", () => {
        activeIdx = -1;
        const query = input.value.trim();
        if (query.length < 2) {
            dropdown.classList.remove("visible");
            return;
        }
        clearTimeout(timeout);
        timeout = setTimeout(async () => {
            try {
                const res = await fetch(
                    `${API_BASE}/routes/stations?search=${encodeURIComponent(query)}&limit=12`
                );
                const stations = await res.json();
                renderDropdown(dropdown, stations, role);
            } catch (err) {
                console.error("Station search error:", err);
            }
        }, 200);
    });

    input.addEventListener("keydown", (e) => {
        const items = dropdown.querySelectorAll(".autocomplete-item");
        if (!items.length) return;

        if (e.key === "ArrowDown") {
            e.preventDefault();
            activeIdx = Math.min(activeIdx + 1, items.length - 1);
            highlightItem(items, activeIdx);
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            activeIdx = Math.max(activeIdx - 1, 0);
            highlightItem(items, activeIdx);
        } else if (e.key === "Enter" && activeIdx >= 0) {
            e.preventDefault();
            items[activeIdx].click();
        } else if (e.key === "Escape") {
            dropdown.classList.remove("visible");
        }
    });
}

function highlightItem(items, idx) {
    items.forEach((item, i) => item.classList.toggle("active", i === idx));
    if (idx >= 0 && items[idx]) items[idx].scrollIntoView({ block: "nearest" });
}

function renderDropdown(dropdown, stations, role) {
    while (dropdown.firstChild) dropdown.removeChild(dropdown.firstChild);

    if (stations.length === 0) {
        const empty = document.createElement("div");
        empty.className = "autocomplete-item";
        empty.style.color = "var(--text-muted)";
        empty.textContent = "Aucune gare trouvee";
        dropdown.appendChild(empty);
        dropdown.classList.add("visible");
        return;
    }

    stations.forEach((station) => {
        const item = document.createElement("div");
        item.className = "autocomplete-item";

        const name = document.createElement("div");
        name.className = "autocomplete-item-name";
        name.textContent = station.station_name;

        const detail = document.createElement("div");
        detail.className = "autocomplete-item-detail";
        detail.textContent = `${station.commune || ""} (${station.department || ""})`;

        item.appendChild(name);
        item.appendChild(detail);
        item.addEventListener("click", () => onStationSelected(station, role));
        dropdown.appendChild(item);
    });

    dropdown.classList.add("visible");
}

function onStationSelected(station, role) {
    // Mettre a jour l'input
    const wrapper = document.querySelector(`.autocomplete-wrapper[data-role="${role}"]`);
    const input = wrapper.querySelector(".station-input");
    const dropdown = wrapper.querySelector(".autocomplete-dropdown");
    input.value = station.station_name;
    dropdown.classList.remove("visible");

    // Stocker la selection
    _route[role] = station;

    // Si les deux gares sont selectionnees, trouver la ligne commune
    if (_route.departure && _route.arrival) {
        findAndShowRoute();
    } else if (_route.departure) {
        // Zoom sur la gare de depart
        if (station.latitude && station.longitude) {
            map.flyTo({ center: [station.longitude, station.latitude], zoom: 8, duration: 1 });
        }
    }
}

async function findAndShowRoute() {
    const dep = _route.departure;
    const arr = _route.arrival;
    const depLines = (dep.line_codes || "").split(",").filter(Boolean);
    const arrLines = (arr.line_codes || "").split(",").filter(Boolean);

    // Chercher une ligne en commun (trajet direct)
    const common = depLines.filter((l) => arrLines.includes(l));

    document.getElementById("btn-clear-route").style.display = "block";

    if (common.length > 0) {
        // Trajet direct
        await showDirectRoute(common[0], dep, arr);
    } else {
        // Pas de trajet direct : chercher les correspondances
        await findTransfers(depLines, arrLines, dep, arr);
    }
}

function _stationMarker(name, lat, lon, role) {
    return {
        type: "Feature",
        geometry: { type: "Point", coordinates: [lon, lat] },
        properties: { name, role },
    };
}

async function _fetchSegment(lineId, fromLat, fromLon, toLat, toLon) {
    const params = new URLSearchParams({
        line_id: lineId,
        from_lat: fromLat.toString(),
        from_lon: fromLon.toString(),
        to_lat: toLat.toString(),
        to_lon: toLon.toString(),
    });
    const res = await fetch(`${API_BASE}/routes/segment?${params}`);
    return res.json();
}

async function showDirectRoute(lineId, dep, arr) {
    _route.selectedLineId = lineId;
    _route.transferLineId = null;
    _route.arrLineId = null;
    document.getElementById("btn-analyze-route").disabled = false;

    try {
        const segUrl = `${API_BASE}/routes/segment?line_id=${lineId}&from_lat=${dep.latitude}&from_lon=${dep.longitude}&to_lat=${arr.latitude}&to_lon=${arr.longitude}`;
        drawRoute(
            [segUrl],
            [
                { name: dep.station_name, lat: dep.latitude, lon: dep.longitude, role: "departure" },
                { name: arr.station_name, lat: arr.latitude, lon: arr.longitude, role: "arrival" },
            ]
        );

        const infoDiv = document.getElementById("selected-line-info");
        while (infoDiv.firstChild) infoDiv.removeChild(infoDiv.firstChild);

        const segKm = geojson.features[0]?.properties?.length_km || "?";
        const lineName = document.createElement("div");
        lineName.className = "line-name";
        lineName.textContent = `${dep.station_name} → ${arr.station_name}`;
        infoDiv.appendChild(lineName);

        const lineDetail = document.createElement("div");
        lineDetail.className = "line-detail";
        lineDetail.textContent = `Trajet direct — ${segKm} km`;
        infoDiv.appendChild(lineDetail);
        infoDiv.style.display = "block";
    } catch (err) {
        console.error("Direct route error:", err);
    }
}

async function findTransfers(depLines, arrLines, dep, arr) {
    const infoDiv = document.getElementById("selected-line-info");
    while (infoDiv.firstChild) infoDiv.removeChild(infoDiv.firstChild);

    const loading = document.createElement("div");
    loading.className = "line-detail";
    loading.textContent = "Recherche de correspondances...";
    infoDiv.appendChild(loading);
    infoDiv.style.display = "block";

    try {
        const params = new URLSearchParams({
            dep_lines: depLines.join(","),
            arr_lines: arrLines.join(","),
            dep_lat: dep.latitude.toString(),
            dep_lon: dep.longitude.toString(),
            arr_lat: arr.latitude.toString(),
            arr_lon: arr.longitude.toString(),
        });
        const res = await fetch(`${API_BASE}/routes/transfers?${params}`);
        const transfers = await res.json();

        while (infoDiv.firstChild) infoDiv.removeChild(infoDiv.firstChild);

        if (transfers.length === 0) {
            const noRoute = document.createElement("div");
            noRoute.className = "line-detail";
            noRoute.textContent = "Aucune correspondance trouvee.";
            infoDiv.appendChild(noRoute);
            return;
        }

        const header = document.createElement("div");
        header.className = "line-name";
        header.textContent = `${dep.station_name} → ${arr.station_name}`;
        infoDiv.appendChild(header);

        const hint = document.createElement("div");
        hint.className = "line-detail";
        hint.textContent = "Correspondances disponibles :";
        infoDiv.appendChild(hint);

        const list = document.createElement("div");
        list.style.cssText = "margin-top:6px";

        transfers.forEach((t) => {
            const option = document.createElement("div");
            option.className = "transfer-option";

            const label = document.createElement("span");
            const stationLabel = t.transfer_station
                ? `via ${t.transfer_station}`
                : (t.line_name || `Ligne ${t.line_id}`);
            label.textContent = stationLabel;

            const km = document.createElement("span");
            km.className = "transfer-km";
            km.textContent = `${t.length_km} km`;

            option.appendChild(label);
            option.appendChild(km);
            option.addEventListener("click", () => {
                list.querySelectorAll(".transfer-option").forEach((o) =>
                    o.classList.remove("selected")
                );
                option.classList.add("selected");
                selectTransferRoute(depLines[0], t.line_id, arrLines[0], dep, arr, t);
            });
            list.appendChild(option);
        });

        infoDiv.appendChild(list);
    } catch (err) {
        console.error("Transfer search error:", err);
    }
}

async function selectTransferRoute(depLineId, transferLineId, arrLineId, dep, arr, transferInfo) {
    _route.selectedLineId = depLineId;
    _route.transferLineId = transferLineId;
    _route.arrLineId = arrLineId;
    document.getElementById("btn-analyze-route").disabled = false;

    const tLat = transferInfo.transfer_lat;
    const tLon = transferInfo.transfer_lon;

    if (!tLat || !tLon) {
        console.error("Transfer station coordinates missing");
        return;
    }

    try {
        const segUrl1 = `${API_BASE}/routes/segment?line_id=${depLineId}&from_lat=${dep.latitude}&from_lon=${dep.longitude}&to_lat=${tLat}&to_lon=${tLon}`;
        const segUrl2 = `${API_BASE}/routes/segment?line_id=${arrLineId}&from_lat=${tLat}&from_lon=${tLon}&to_lat=${arr.latitude}&to_lon=${arr.longitude}`;

        drawRoute(
            [segUrl1, segUrl2],
            [
                { name: dep.station_name, lat: dep.latitude, lon: dep.longitude, role: "departure" },
                { name: transferInfo.transfer_station, lat: tLat, lon: tLon, role: "transfer" },
                { name: arr.station_name, lat: arr.latitude, lon: arr.longitude, role: "arrival" },
            ]
        );
    } catch (err) {
        console.error("Transfer route display error:", err);
    }
}

async function analyzeRoute() {
    if (!_route.selectedLineId) return;

    const tech = document.getElementById("route-tech-select").value;
    const resultsDiv = document.getElementById("route-results");
    const btn = document.getElementById("btn-analyze-route");

    btn.disabled = true;
    btn.textContent = "...";
    while (resultsDiv.firstChild) resultsDiv.removeChild(resultsDiv.firstChild);

    // Analyser les lignes reelles du trajet (dep + arr, pas la ligne-pont)
    const lineIds = [_route.selectedLineId];
    if (_route.arrLineId && _route.arrLineId !== _route.selectedLineId) {
        lineIds.push(_route.arrLineId);
    }

    try {
        // Lancer les analyses en parallele
        const results = await Promise.all(
            lineIds.map((id) =>
                fetch(`${API_BASE}/routes/coverage`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ line_id: id, technology: tech }),
                }).then((r) => r.json())
            )
        );

        // Agreger : pour chaque operateur, moyenne ponderee par longueur
        const byOp = {};
        let totalKm = 0;
        results.forEach((coverage) => {
            coverage.forEach((r) => {
                if (!byOp[r.operator]) {
                    byOp[r.operator] = { operator: r.operator, operator_name: r.operator_name, covKm: 0, totalKm: 0 };
                }
                byOp[r.operator].covKm += r.covered_length_km;
                byOp[r.operator].totalKm += r.total_length_km;
            });
        });

        const merged = Object.values(byOp).map((r) => ({
            operator: r.operator,
            operator_name: r.operator_name,
            total_length_km: Math.round(r.totalKm * 10) / 10,
            covered_length_km: Math.round(r.covKm * 10) / 10,
            coverage_pct: Math.round((r.covKm / (r.totalKm || 1)) * 1000) / 10,
        }));
        merged.sort((a, b) => b.coverage_pct - a.coverage_pct);

        displayRouteResults(merged, resultsDiv);
        if (merged.length > 0) updateRouteCoverageChart(merged);
    } catch (err) {
        console.error("Route analysis error:", err);
        const errEl = document.createElement("div");
        errEl.className = "panel-hint";
        errEl.textContent = "Erreur lors de l'analyse.";
        resultsDiv.appendChild(errEl);
    } finally {
        btn.disabled = false;
        btn.textContent = "Analyser";
    }
}

function displayRouteResults(coverage, container) {
    while (container.firstChild) container.removeChild(container.firstChild);

    if (coverage.length === 0) {
        const empty = document.createElement("div");
        empty.className = "panel-hint";
        empty.textContent = "Aucune donnee de couverture pour cette ligne.";
        container.appendChild(empty);
        return;
    }

    coverage.forEach((r) => {
        const row = document.createElement("div");
        row.className = "stat-mini";

        const label = document.createElement("span");
        label.className = "stat-mini-label";
        const opInfo = APP_OPERATORS[r.operator];
        if (opInfo) {
            const dot = document.createElement("span");
            dot.style.cssText = `display:inline-block;width:8px;height:8px;border-radius:50%;background:${opInfo.color};margin-right:6px`;
            label.appendChild(dot);
        }
        const nameSpan = document.createElement("span");
        nameSpan.textContent = r.operator_name || r.operator;
        label.appendChild(nameSpan);

        const value = document.createElement("span");
        value.className = "stat-mini-value";
        value.textContent = `${r.coverage_pct}%`;

        row.appendChild(label);
        row.appendChild(value);
        container.appendChild(row);
    });

    const detail = document.createElement("div");
    detail.className = "panel-hint";
    const totalKm = coverage[0].total_length_km;
    detail.textContent = `Longueur : ${totalKm} km`;
    container.appendChild(detail);
}

function clearRoute() {
    _route.departure = null;
    _route.arrival = null;
    _route.selectedLineId = null;
    _route.transferLineId = null;
    _route.arrLineId = null;

    document.querySelectorAll(".station-input").forEach((input) => { input.value = ""; });
    document.getElementById("selected-line-info").style.display = "none";
    document.getElementById("btn-analyze-route").disabled = true;
    document.getElementById("btn-clear-route").style.display = "none";

    const resultsDiv = document.getElementById("route-results");
    while (resultsDiv.firstChild) resultsDiv.removeChild(resultsDiv.firstChild);

    const card = document.getElementById("route-chart-card");
    if (card) card.style.display = "none";

    if (typeof clearRouteLine === "function") clearRouteLine();
}
