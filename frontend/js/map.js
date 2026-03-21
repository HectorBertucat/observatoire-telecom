/* Carte MapLibre GL JS — dark theme + CartoDB Positron */

const protocol = new pmtiles.Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);

const OPERATORS = {
    OF:   { name: "Orange",           color: "#f97316" },
    BYT:  { name: "Bouygues Telecom", color: "#3b82f6" },
    FREE: { name: "Free Mobile",      color: "#ec4899" },
    SFR:  { name: "SFR",              color: "#ef4444" },
};

const map = new maplibregl.Map({
    container: "map",
    style: {
        version: 8,
        sources: {
            basemap: {
                type: "raster",
                tiles: [
                    "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
                    "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
                ],
                tileSize: 256,
                attribution: "&copy; CARTO &copy; OpenStreetMap",
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
            {
                id: "basemap",
                type: "raster",
                source: "basemap",
                minzoom: 0,
                maxzoom: 19,
            },
            ...Object.entries(OPERATORS).flatMap(([op, info]) => [
                {
                    id: `coverage-fill-${op}`,
                    type: "fill",
                    source: "coverage",
                    "source-layer": "coverage",
                    filter: ["==", ["get", "operator"], op],
                    paint: {
                        "fill-color": info.color,
                        "fill-opacity": 0.3,
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
                        "line-width": ["interpolate", ["linear"], ["zoom"], 4, 0.3, 10, 1],
                        "line-opacity": 0.5,
                    },
                },
            ]),
            ...Object.entries(OPERATORS).map(([op, info]) => ({
                id: `antennas-${op}`,
                type: "circle",
                source: "antennas",
                "source-layer": "antennas",
                filter: ["==", ["get", "operator"], op],
                minzoom: 8,
                paint: {
                    "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, 1.5, 11, 3, 14, 6],
                    "circle-color": info.color,
                    "circle-stroke-color": "rgba(255,255,255,0.6)",
                    "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 8, 0, 11, 0.5, 14, 1],
                    "circle-opacity": 0.8,
                },
            })),
        ],
    },
    center: [2.888, 46.603],
    zoom: 5.5,
    maxZoom: 15,
});

map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

// Popup click — antennas first, then coverage
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
            `<div style="color:#94a3b8;margin-bottom:4px">${coverageFeats[0].properties.technology || "4G"}</div>` +
            lines.join("<br>") + `</div>`
        )
        .addTo(map);
});

// Right-click → nearby antennas
map.on("contextmenu", async (e) => {
    e.preventDefault();
    const { lng, lat } = e.lngLat;
    try {
        const res = await fetch(`/api/v1/antennas/nearby?lat=${lat.toFixed(5)}&lon=${lng.toFixed(5)}&radius=2&limit=10`);
        const data = await res.json();
        if (data.length === 0) {
            new maplibregl.Popup({ maxWidth: "250px", className: "dark-popup" })
                .setLngLat(e.lngLat)
                .setHTML(`<div style="font-size:12px;color:#94a3b8">Aucune antenne dans 2km</div>`)
                .addTo(map);
            return;
        }
        const byOp = {};
        data.forEach((a) => { byOp[a.operator] = (byOp[a.operator] || 0) + 1; });
        const opLines = Object.entries(byOp).map(([op, count]) => {
            const info = OPERATORS[op] || { name: op, color: "#999" };
            return `<span style="color:${info.color}">&#9679;</span> ${info.name}: ${count}`;
        }).join("<br>");
        new maplibregl.Popup({ maxWidth: "250px", className: "dark-popup" })
            .setLngLat(e.lngLat)
            .setHTML(
                `<div style="font-size:12px">` +
                `<b>${data.length} antennes</b> dans 2km<br>` +
                `<span style="color:#64748b">Plus proche: ${data[0].distance_km}km</span>` +
                `<hr style="margin:4px 0;border:none;border-top:1px solid rgba(255,255,255,0.1)">` +
                opLines + `</div>`
            )
            .addTo(map);
    } catch (err) { console.error("Nearby error:", err); }
});

// Cursor pointer
for (const op of Object.keys(OPERATORS)) {
    for (const prefix of ["coverage-fill-", "antennas-"]) {
        map.on("mouseenter", `${prefix}${op}`, () => { map.getCanvas().style.cursor = "pointer"; });
        map.on("mouseleave", `${prefix}${op}`, () => { map.getCanvas().style.cursor = ""; });
    }
}

function filterByOperator(operator) {
    for (const op of Object.keys(OPERATORS)) {
        const visible = operator === "all" || operator === op;
        const vis = visible ? "visible" : "none";
        map.setLayoutProperty(`coverage-fill-${op}`, "visibility", vis);
        map.setLayoutProperty(`coverage-line-${op}`, "visibility", vis);
        map.setLayoutProperty(`antennas-${op}`, "visibility", vis);
    }
}

function toggleOperator(op, visible) {
    const vis = visible ? "visible" : "none";
    map.setLayoutProperty(`coverage-fill-${op}`, "visibility", vis);
    map.setLayoutProperty(`coverage-line-${op}`, "visibility", vis);
    map.setLayoutProperty(`antennas-${op}`, "visibility", vis);
}

function filterTechnology(tech) {
    for (const op of Object.keys(OPERATORS)) {
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

// Zoom indicator
map.on("zoomend", () => {
    const el = document.getElementById("zoom-indicator");
    if (el) el.textContent = `z${map.getZoom().toFixed(1)}`;
});

// Build legend
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
