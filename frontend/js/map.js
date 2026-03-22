/* Carte MapLibre GL JS — dark pro theme */

const protocol = new pmtiles.Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);

const OPERATORS = {
    OF:   { name: "Orange",           color: "#f97316", colorLight: "rgba(249,115,22,0.15)" },
    BYT:  { name: "Bouygues Telecom", color: "#3b82f6", colorLight: "rgba(59,130,246,0.15)" },
    FREE: { name: "Free Mobile",      color: "#ec4899", colorLight: "rgba(236,72,153,0.15)" },
    SFR:  { name: "SFR",              color: "#ef4444", colorLight: "rgba(239,68,68,0.15)" },
};

let activeOperator = "all";

const map = new maplibregl.Map({
    container: "map",
    style: {
        version: 8,
        glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
        sources: {
            basemap: {
                type: "raster",
                tiles: [
                    "https://a.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}@2x.png",
                    "https://b.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}@2x.png",
                ],
                tileSize: 256,
                attribution: "&copy; CARTO &copy; OpenStreetMap",
            },
            labels: {
                type: "raster",
                tiles: [
                    "https://a.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}@2x.png?lang=fr",
                    "https://b.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}@2x.png?lang=fr",
                ],
                tileSize: 256,
            },
            coverage: { type: "vector", url: "pmtiles:///tiles/coverage.pmtiles" },
            antennas: { type: "vector", url: "pmtiles:///tiles/antennas.pmtiles" },
        },
        layers: [
            { id: "basemap", type: "raster", source: "basemap", minzoom: 0, maxzoom: 19 },
            ...Object.entries(OPERATORS).flatMap(([op, info]) => [
                {
                    id: `coverage-fill-${op}`, type: "fill", source: "coverage",
                    "source-layer": "coverage", filter: ["==", ["get", "operator"], op],
                    paint: { "fill-color": info.color, "fill-opacity": 0.25 },
                },
                {
                    id: `coverage-line-${op}`, type: "line", source: "coverage",
                    "source-layer": "coverage", filter: ["==", ["get", "operator"], op],
                    paint: {
                        "line-color": info.color,
                        "line-width": ["interpolate", ["linear"], ["zoom"], 4, 0.2, 8, 0.5, 12, 1, 14, 1.5],
                        "line-opacity": 0.4,
                    },
                },
            ]),
            { id: "labels", type: "raster", source: "labels", minzoom: 0, maxzoom: 19 },
            ...Object.entries(OPERATORS).map(([op, info]) => ({
                id: `antennas-${op}`, type: "circle", source: "antennas",
                "source-layer": "antennas", filter: ["==", ["get", "operator"], op], minzoom: 9,
                paint: {
                    "circle-radius": ["interpolate", ["linear"], ["zoom"], 9, 1.5, 11, 2.5, 13, 4, 15, 7],
                    "circle-color": info.color,
                    "circle-stroke-color": "rgba(255,255,255,0.7)",
                    "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 9, 0, 11, 0.5, 14, 1],
                    "circle-opacity": 0.85,
                },
            })),
            ...Object.entries(OPERATORS).map(([op, info]) => ({
                id: `antennas-5g-halo-${op}`, type: "circle", source: "antennas",
                "source-layer": "antennas",
                filter: ["all", ["==", ["get", "operator"], op], ["==", ["get", "technology"], "5G"]],
                minzoom: 10,
                paint: {
                    "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, 6, 12, 12, 14, 25],
                    "circle-color": info.color, "circle-opacity": 0.08, "circle-stroke-width": 0,
                },
            })),
        ],
    },
    center: [2.888, 46.603], zoom: 5.5, maxZoom: 16,
});

map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

/* === INTERACTIONS === */

map.on("click", (e) => {
    const antennaLayers = Object.keys(OPERATORS).map((op) => `antennas-${op}`);
    const antennaFeats = map.queryRenderedFeatures(e.point, { layers: antennaLayers });
    if (antennaFeats.length > 0) {
        const p = antennaFeats[0].properties;
        const info = OPERATORS[p.operator] || { name: p.operator, color: "#999" };
        new maplibregl.Popup({ maxWidth: "220px", className: "dark-popup" })
            .setLngLat(e.lngLat)
            .setHTML(`<b style="color:${info.color}">${info.name}</b><br>${p.technology} — ${p.commune || ""}`)
            .addTo(map);
        return;
    }
    const coverageLayers = Object.keys(OPERATORS).map((op) => `coverage-fill-${op}`);
    const coverageFeats = map.queryRenderedFeatures(e.point, { layers: coverageLayers });
    if (coverageFeats.length === 0) return;
    const ops = [...new Set(coverageFeats.map((f) => f.properties.operator))];
    const lines = ops.map((op) => {
        const info = OPERATORS[op];
        return `<span style="color:${info.color}">&#9679;</span> ${info.name}`;
    });
    new maplibregl.Popup({ maxWidth: "220px", className: "dark-popup" })
        .setLngLat(e.lngLat)
        .setHTML(`<div style="font-size:12px"><div style="color:#94a3b8;margin-bottom:4px">${coverageFeats[0].properties.technology || ""}</div>${lines.join("<br>")}</div>`)
        .addTo(map);
});

map.on("contextmenu", async (e) => {
    e.preventDefault();
    const { lng, lat } = e.lngLat;
    try {
        const res = await fetch(`/api/v1/antennas/nearby?lat=${lat.toFixed(5)}&lon=${lng.toFixed(5)}&radius=2&limit=15`);
        const data = await res.json();
        if (data.length === 0) {
            new maplibregl.Popup({ maxWidth: "250px", className: "dark-popup" })
                .setLngLat(e.lngLat).setHTML(`<div style="font-size:12px;color:#94a3b8">Aucune antenne dans 2km</div>`).addTo(map);
            return;
        }
        const byOp = {}, byTech = {};
        data.forEach((a) => { byOp[a.operator] = (byOp[a.operator] || 0) + 1; byTech[a.technology] = (byTech[a.technology] || 0) + 1; });
        const opLines = Object.entries(byOp).map(([op, count]) => {
            const info = OPERATORS[op] || { name: op, color: "#999" };
            return `<span style="color:${info.color}">&#9679;</span> ${info.name}: ${count}`;
        }).join("<br>");
        const techLine = Object.entries(byTech).map(([t, c]) => `${t}:${c}`).join(" · ");
        new maplibregl.Popup({ maxWidth: "260px", className: "dark-popup" })
            .setLngLat(e.lngLat)
            .setHTML(`<div style="font-size:12px"><b>${data.length} antennes</b> dans 2km<span style="color:#64748b;margin-left:6px">${techLine}</span><br><span style="color:#64748b">Plus proche: ${data[0].operator} ${data[0].technology} (${data[0].distance_km}km)</span><hr style="margin:5px 0;border:none;border-top:1px solid rgba(255,255,255,0.1)">${opLines}</div>`)
            .addTo(map);
    } catch (err) { console.error("Nearby error:", err); }
});

for (const op of Object.keys(OPERATORS)) {
    for (const prefix of ["coverage-fill-", "antennas-"]) {
        map.on("mouseenter", `${prefix}${op}`, () => { map.getCanvas().style.cursor = "pointer"; });
        map.on("mouseleave", `${prefix}${op}`, () => { map.getCanvas().style.cursor = ""; });
    }
}

/* === OPERATOR HIGHLIGHT MODE === */
function setOperatorHighlight(operator) {
    activeOperator = operator;
    for (const op of Object.keys(OPERATORS)) {
        const isActive = operator === "all" || operator === op;
        map.setPaintProperty(`coverage-fill-${op}`, "fill-opacity", isActive ? (operator === "all" ? 0.25 : 0.45) : 0.05);
        map.setPaintProperty(`coverage-line-${op}`, "line-opacity", isActive ? (operator === "all" ? 0.4 : 0.7) : 0.05);
        map.setPaintProperty(`antennas-${op}`, "circle-opacity", isActive ? 0.85 : 0.15);
        map.setPaintProperty(`antennas-5g-halo-${op}`, "circle-opacity", isActive ? 0.08 : 0.01);
    }
}

function toggleOperator(op, visible) {
    const vis = visible ? "visible" : "none";
    [`coverage-fill-${op}`, `coverage-line-${op}`, `antennas-${op}`, `antennas-5g-halo-${op}`].forEach((id) =>
        map.setLayoutProperty(id, "visibility", vis)
    );
}

function filterTechnologyOnMap(tech) {
    for (const op of Object.keys(OPERATORS)) {
        const baseFilter = ["==", ["get", "operator"], op];
        const filter = tech === "all" ? baseFilter : ["all", baseFilter, ["==", ["get", "technology"], tech]];
        map.setFilter(`coverage-fill-${op}`, filter);
        map.setFilter(`coverage-line-${op}`, filter);
    }
}

/* === ROUTE LINE DISPLAY === */
// Utilise des MapLibre Markers (DOM) pour les gares et des sources GeoJSON
// par URL pour les lignes. Evite le bug MapLibre ou setData/removeSource+addSource
// ne genere pas de tuiles dans les contextes async.

let _routeMarkers = [];
let _routeSources = [];

function _addRouteLineSource(id, url) {
    map.addSource(id, { type: "geojson", data: url });
    map.addLayer({ id: id + "-bdr", type: "line", source: id,
        layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": "#1e293b", "line-width": 7, "line-opacity": 0.9 } });
    map.addLayer({ id: id + "-ln", type: "line", source: id,
        layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": "#e2e8f0", "line-width": 3, "line-opacity": 0.9 } });
    map.addLayer({ id: id + "-dsh", type: "line", source: id,
        layout: { "line-cap": "butt" },
        paint: { "line-color": "#3b82f6", "line-width": 3, "line-dasharray": [2, 3], "line-opacity": 0.8 } });
    _routeSources.push(id);
}

function _addStationMarker(name, lat, lon, role) {
    const colors = { departure: "#10b981", arrival: "#ef4444", transfer: "#f59e0b" };
    const el = document.createElement("div");
    el.style.cssText = `width:16px;height:16px;border-radius:50%;background:${colors[role] || "#3b82f6"};border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.4);cursor:default`;
    const marker = new maplibregl.Marker({ element: el })
        .setLngLat([lon, lat])
        .setPopup(new maplibregl.Popup({ offset: 12, className: "dark-popup" }).setText(name))
        .addTo(map);
    _routeMarkers.push(marker);
}

function drawRoute(segments, stations) {
    clearRouteLine();

    // Zoom d'abord sur la zone des gares
    if (stations.length >= 2) {
        const lngs = stations.map((s) => s.lon);
        const lats = stations.map((s) => s.lat);
        map.fitBounds(
            [[Math.min(...lngs) - 0.5, Math.min(...lats) - 0.3],
             [Math.max(...lngs) + 0.5, Math.max(...lats) + 0.3]],
            { padding: 40, animate: false }
        );
    }

    // Ajouter les sources GeoJSON par URL (fiable dans MapLibre)
    segments.forEach((url, i) => {
        _addRouteLineSource("rt" + i, url);
    });

    // Ajouter les marqueurs de gare (DOM, toujours fiable)
    stations.forEach((s) => {
        _addStationMarker(s.name, s.lat, s.lon, s.role);
    });
}

function clearRouteLine() {
    // Supprimer les marqueurs
    _routeMarkers.forEach((m) => m.remove());
    _routeMarkers = [];
    // Supprimer les sources/layers
    _routeSources.forEach((id) => {
        ["-bdr", "-ln", "-dsh"].forEach((suf) => { if (map.getLayer(id + suf)) map.removeLayer(id + suf); });
        if (map.getSource(id)) map.removeSource(id);
    });
    _routeSources = [];
}

/* === ZOOM INDICATOR === */
map.on("zoomend", () => {
    const el = document.getElementById("zoom-indicator");
    if (el) el.textContent = `z${map.getZoom().toFixed(1)}`;
});

/* === LEGEND === */
map.on("load", () => {
    const container = document.getElementById("map-legend");
    if (!container) return;
    for (const [op, info] of Object.entries(OPERATORS)) {
        const item = document.createElement("label");
        item.className = "legend-item";
        const cb = document.createElement("input");
        cb.type = "checkbox"; cb.checked = true;
        cb.addEventListener("change", () => toggleOperator(op, cb.checked));
        const swatch = document.createElement("span");
        swatch.className = "legend-swatch"; swatch.style.backgroundColor = info.color;
        const label = document.createElement("span");
        label.className = "legend-label"; label.textContent = info.name;
        item.appendChild(cb); item.appendChild(swatch); item.appendChild(label);
        container.appendChild(item);
    }
});
