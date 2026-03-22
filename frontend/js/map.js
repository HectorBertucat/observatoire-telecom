/* Carte MapLibre GL JS — dark pro theme */

const protocol = new pmtiles.Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);

const OPERATORS = {
    OF:   { name: "Orange",           color: "#f97316", colorLight: "rgba(249,115,22,0.15)" },
    BYT:  { name: "Bouygues Telecom", color: "#3b82f6", colorLight: "rgba(59,130,246,0.15)" },
    FREE: { name: "Free Mobile",      color: "#ec4899", colorLight: "rgba(236,72,153,0.15)" },
    SFR:  { name: "SFR",              color: "#ef4444", colorLight: "rgba(239,68,68,0.15)" },
};

let activeOperator = "all"; // "all" or specific operator code

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
            coverage: {
                type: "vector",
                url: "pmtiles:///tiles/coverage.pmtiles",
            },
            antennas: {
                type: "vector",
                url: "pmtiles:///tiles/antennas.pmtiles",
            },
        },
        layers: [
            // Basemap sans labels (sous la couverture)
            {
                id: "basemap",
                type: "raster",
                source: "basemap",
                minzoom: 0,
                maxzoom: 19,
            },
            // Couverture polygones par opérateur
            ...Object.entries(OPERATORS).flatMap(([op, info]) => [
                {
                    id: `coverage-fill-${op}`,
                    type: "fill",
                    source: "coverage",
                    "source-layer": "coverage",
                    filter: ["==", ["get", "operator"], op],
                    paint: {
                        "fill-color": info.color,
                        "fill-opacity": 0.25,
                    },
                },
                {
                    id: `coverage-line-${op}`,
                    type: "line",
                    source: "coverage",
                    "source-layer": "coverage",
                    filter: ["==", ["get", "operator"], op],
                    paint: {
                        "line-color": info.color,
                        "line-width": [
                            "interpolate", ["linear"], ["zoom"],
                            4, 0.2, 8, 0.5, 12, 1, 14, 1.5,
                        ],
                        "line-opacity": 0.4,
                    },
                },
            ]),
            // Labels au-dessus de la couverture
            {
                id: "labels",
                type: "raster",
                source: "labels",
                minzoom: 0,
                maxzoom: 19,
            },
            // Antennes : cercles par opérateur
            ...Object.entries(OPERATORS).map(([op, info]) => ({
                id: `antennas-${op}`,
                type: "circle",
                source: "antennas",
                "source-layer": "antennas",
                filter: ["==", ["get", "operator"], op],
                minzoom: 9,
                paint: {
                    "circle-radius": [
                        "interpolate", ["linear"], ["zoom"],
                        9, 1.5, 11, 2.5, 13, 4, 15, 7,
                    ],
                    "circle-color": info.color,
                    "circle-stroke-color": "rgba(255,255,255,0.7)",
                    "circle-stroke-width": [
                        "interpolate", ["linear"], ["zoom"],
                        9, 0, 11, 0.5, 14, 1,
                    ],
                    "circle-opacity": 0.85,
                },
            })),
            // 5G antennes avec halo plus grand (proxy couverture)
            ...Object.entries(OPERATORS).map(([op, info]) => ({
                id: `antennas-5g-halo-${op}`,
                type: "circle",
                source: "antennas",
                "source-layer": "antennas",
                filter: [
                    "all",
                    ["==", ["get", "operator"], op],
                    ["==", ["get", "technology"], "5G"],
                ],
                minzoom: 10,
                paint: {
                    "circle-radius": [
                        "interpolate", ["linear"], ["zoom"],
                        10, 6, 12, 12, 14, 25,
                    ],
                    "circle-color": info.color,
                    "circle-opacity": 0.08,
                    "circle-stroke-width": 0,
                },
            })),
        ],
    },
    center: [2.888, 46.603],
    zoom: 5.5,
    maxZoom: 16,
});

map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

/* === INTERACTIONS === */

// Click popup
map.on("click", (e) => {
    const antennaLayers = Object.keys(OPERATORS).map((op) => `antennas-${op}`);
    const antennaFeats = map.queryRenderedFeatures(e.point, { layers: antennaLayers });

    if (antennaFeats.length > 0) {
        const p = antennaFeats[0].properties;
        const info = OPERATORS[p.operator] || { name: p.operator, color: "#999" };
        new maplibregl.Popup({ maxWidth: "220px", className: "dark-popup" })
            .setLngLat(e.lngLat)
            .setHTML(
                `<b style="color:${info.color}">${info.name}</b><br>` +
                `${p.technology} — ${p.commune || ""}`
            )
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
        .setHTML(
            `<div style="font-size:12px">` +
            `<div style="color:#94a3b8;margin-bottom:4px">${coverageFeats[0].properties.technology || ""}</div>` +
            lines.join("<br>") + `</div>`
        )
        .addTo(map);
});

// Right-click nearby
map.on("contextmenu", async (e) => {
    e.preventDefault();
    const { lng, lat } = e.lngLat;
    try {
        const res = await fetch(`/api/v1/antennas/nearby?lat=${lat.toFixed(5)}&lon=${lng.toFixed(5)}&radius=2&limit=15`);
        const data = await res.json();
        if (data.length === 0) {
            new maplibregl.Popup({ maxWidth: "250px", className: "dark-popup" })
                .setLngLat(e.lngLat)
                .setHTML(`<div style="font-size:12px;color:#94a3b8">Aucune antenne dans 2km</div>`)
                .addTo(map);
            return;
        }
        const byOp = {};
        const byTech = {};
        data.forEach((a) => {
            byOp[a.operator] = (byOp[a.operator] || 0) + 1;
            byTech[a.technology] = (byTech[a.technology] || 0) + 1;
        });
        const opLines = Object.entries(byOp).map(([op, count]) => {
            const info = OPERATORS[op] || { name: op, color: "#999" };
            return `<span style="color:${info.color}">&#9679;</span> ${info.name}: ${count}`;
        }).join("<br>");
        const techLine = Object.entries(byTech).map(([t, c]) => `${t}:${c}`).join(" · ");

        new maplibregl.Popup({ maxWidth: "260px", className: "dark-popup" })
            .setLngLat(e.lngLat)
            .setHTML(
                `<div style="font-size:12px">` +
                `<b>${data.length} antennes</b> dans 2km` +
                `<span style="color:#64748b;margin-left:6px">${techLine}</span><br>` +
                `<span style="color:#64748b">Plus proche: ${data[0].operator} ${data[0].technology} (${data[0].distance_km}km)</span>` +
                `<hr style="margin:5px 0;border:none;border-top:1px solid rgba(255,255,255,0.1)">` +
                opLines + `</div>`
            )
            .addTo(map);
    } catch (err) { console.error("Nearby error:", err); }
});

// Cursor
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
        const fillOpacity = isActive ? (operator === "all" ? 0.25 : 0.45) : 0.05;
        const lineOpacity = isActive ? (operator === "all" ? 0.4 : 0.7) : 0.05;

        map.setPaintProperty(`coverage-fill-${op}`, "fill-opacity", fillOpacity);
        map.setPaintProperty(`coverage-line-${op}`, "line-opacity", lineOpacity);

        // Antennes
        const antennaOpacity = isActive ? 0.85 : 0.15;
        map.setPaintProperty(`antennas-${op}`, "circle-opacity", antennaOpacity);

        // 5G halos
        const haloOpacity = isActive ? 0.08 : 0.01;
        map.setPaintProperty(`antennas-5g-halo-${op}`, "circle-opacity", haloOpacity);
    }
}

function toggleOperator(op, visible) {
    const vis = visible ? "visible" : "none";
    map.setLayoutProperty(`coverage-fill-${op}`, "visibility", vis);
    map.setLayoutProperty(`coverage-line-${op}`, "visibility", vis);
    map.setLayoutProperty(`antennas-${op}`, "visibility", vis);
    map.setLayoutProperty(`antennas-5g-halo-${op}`, "visibility", vis);
}

function filterTechnologyOnMap(tech) {
    for (const op of Object.keys(OPERATORS)) {
        const baseFilter = ["==", ["get", "operator"], op];
        if (tech === "all") {
            map.setFilter(`coverage-fill-${op}`, baseFilter);
            map.setFilter(`coverage-line-${op}`, baseFilter);
        } else {
            const filter = ["all", baseFilter, ["==", ["get", "technology"], tech]];
            map.setFilter(`coverage-fill-${op}`, filter);
            map.setFilter(`coverage-line-${op}`, filter);
        }
    }
}

/* === ROUTE LINE DISPLAY === */
const _routeLayers = [
    "route-line-border", "route-line", "route-line-dash",
    "route-stations-circle", "route-stations-border", "route-stations-label",
];

function drawRouteLine(geojson) {
    clearRouteLine();
    if (!geojson || !geojson.features || geojson.features.length === 0) return;

    map.addSource("route", { type: "geojson", data: geojson });

    // Fond sombre large
    map.addLayer({
        id: "route-line-border",
        type: "line",
        source: "route",
        filter: ["==", ["geometry-type"], "LineString"],
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
            "line-color": "#1e293b",
            "line-width": 7,
            "line-opacity": 0.9,
        },
    }, "labels");

    // Ligne blanche semi-transparente
    map.addLayer({
        id: "route-line",
        type: "line",
        source: "route",
        filter: ["==", ["geometry-type"], "LineString"],
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
            "line-color": "#e2e8f0",
            "line-width": 3,
            "line-opacity": 0.9,
        },
    }, "labels");

    // Tirets colores par-dessus (style ferroviaire)
    map.addLayer({
        id: "route-line-dash",
        type: "line",
        source: "route",
        filter: ["==", ["geometry-type"], "LineString"],
        layout: { "line-cap": "butt" },
        paint: {
            "line-color": "#3b82f6",
            "line-width": 3,
            "line-dasharray": [2, 3],
            "line-opacity": 0.8,
        },
    }, "labels");

    // Cercle de fond des marqueurs de gare (bordure)
    map.addLayer({
        id: "route-stations-border",
        type: "circle",
        source: "route",
        filter: ["==", ["geometry-type"], "Point"],
        paint: {
            "circle-radius": 8,
            "circle-color": "#1e293b",
            "circle-stroke-color": "#e2e8f0",
            "circle-stroke-width": 2,
        },
    }, "labels");

    // Cercle interieur colore
    map.addLayer({
        id: "route-stations-circle",
        type: "circle",
        source: "route",
        filter: ["==", ["geometry-type"], "Point"],
        paint: {
            "circle-radius": 5,
            "circle-color": [
                "match", ["get", "role"],
                "departure", "#10b981",
                "arrival", "#ef4444",
                "transfer", "#f59e0b",
                "#3b82f6",
            ],
        },
    }, "labels");

    // Labels des gares
    map.addLayer({
        id: "route-stations-label",
        type: "symbol",
        source: "route",
        filter: ["==", ["geometry-type"], "Point"],
        layout: {
            "text-field": ["get", "name"],
            "text-size": 12,
            "text-font": ["Open Sans Regular"],
            "text-offset": [0, 1.5],
            "text-anchor": "top",
            "text-allow-overlap": true,
        },
        paint: {
            "text-color": "#e2e8f0",
            "text-halo-color": "#0f1729",
            "text-halo-width": 2,
        },
    }, "labels");

    // Zoom sur l'ensemble
    const coords = [];
    geojson.features.forEach((f) => {
        const geom = f.geometry;
        if (geom.type === "Point") {
            coords.push(geom.coordinates);
        } else if (geom.type === "LineString") {
            coords.push(...geom.coordinates);
        } else if (geom.type === "MultiLineString") {
            geom.coordinates.forEach((line) => coords.push(...line));
        }
    });

    if (coords.length > 1) {
        const lngs = coords.map((c) => c[0]);
        const lats = coords.map((c) => c[1]);
        map.fitBounds(
            [[Math.min(...lngs), Math.min(...lats)], [Math.max(...lngs), Math.max(...lats)]],
            { padding: 60, duration: 1.5 }
        );
    }
}

function clearRouteLine() {
    _routeLayers.forEach((id) => { if (map.getLayer(id)) map.removeLayer(id); });
    if (map.getSource("route")) map.removeSource("route");
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
        cb.type = "checkbox";
        cb.checked = true;
        cb.addEventListener("change", () => toggleOperator(op, cb.checked));

        const swatch = document.createElement("span");
        swatch.className = "legend-swatch";
        swatch.style.backgroundColor = info.color;

        const label = document.createElement("span");
        label.className = "legend-label";
        label.textContent = info.name;

        item.appendChild(cb);
        item.appendChild(swatch);
        item.appendChild(label);
        container.appendChild(item);
    }
});
