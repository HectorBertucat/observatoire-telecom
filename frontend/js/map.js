/* Carte MapLibre GL JS avec vector tiles PMTiles */

const protocol = new pmtiles.Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);

const OPERATORS = {
    OF:   { name: "Orange",          color: "#FF6600" },
    BYT:  { name: "Bouygues Telecom", color: "#003DA5" },
    FREE: { name: "Free Mobile",     color: "#CD1719" },
    SFR:  { name: "SFR",            color: "#E4002B" },
};

const map = new maplibregl.Map({
    container: "map",
    style: {
        version: 8,
        sources: {
            osm: {
                type: "raster",
                tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
                tileSize: 256,
                attribution: "&copy; OpenStreetMap contributors",
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
                id: "osm-tiles",
                type: "raster",
                source: "osm",
                minzoom: 0,
                maxzoom: 19,
            },
            // Couverture : fill + line par opérateur
            ...Object.entries(OPERATORS).flatMap(([op, info]) => [
                {
                    id: `coverage-fill-${op}`,
                    type: "fill",
                    source: "coverage",
                    "source-layer": "coverage",
                    filter: ["==", ["get", "operator"], op],
                    paint: {
                        "fill-color": info.color,
                        "fill-opacity": 0.35,
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
                        "line-width": 0.5,
                        "line-opacity": 0.6,
                    },
                },
            ]),
            // Antennes : cercles par opérateur (visibles à partir de z8)
            ...Object.entries(OPERATORS).map(([op, info]) => ({
                id: `antennas-${op}`,
                type: "circle",
                source: "antennas",
                "source-layer": "antennas",
                filter: ["==", ["get", "operator"], op],
                minzoom: 8,
                paint: {
                    "circle-radius": [
                        "interpolate", ["linear"], ["zoom"],
                        8, 2,
                        10, 3,
                        12, 5,
                        14, 7,
                    ],
                    "circle-color": info.color,
                    "circle-stroke-color": "#fff",
                    "circle-stroke-width": [
                        "interpolate", ["linear"], ["zoom"],
                        8, 0,
                        10, 0.5,
                        12, 1,
                    ],
                    "circle-opacity": 0.8,
                },
            })),
        ],
    },
    center: [2.888, 46.603],
    zoom: 5.5,
    maxZoom: 15,
});

// Navigation controls
map.addControl(new maplibregl.NavigationControl(), "top-right");

// Popup au clic — couverture
map.on("click", (e) => {
    // Chercher antennes d'abord (plus précis)
    const antennaLayers = Object.keys(OPERATORS).map((op) => `antennas-${op}`);
    const antennaFeats = map.queryRenderedFeatures(e.point, { layers: antennaLayers });

    if (antennaFeats.length > 0) {
        const props = antennaFeats[0].properties;
        const info = OPERATORS[props.operator] || { name: props.operator, color: "#999" };
        new maplibregl.Popup({ maxWidth: "250px" })
            .setLngLat(e.lngLat)
            .setHTML(
                `<div style="font-size:13px">` +
                `<b>${info.name}</b> — Antenne ${props.technology}<br>` +
                `<span style="color:#666">Commune: ${props.commune || "?"}</span>` +
                `</div>`
            )
            .addTo(map);
        return;
    }

    // Sinon couverture
    const coverageLayers = Object.keys(OPERATORS).map((op) => `coverage-fill-${op}`);
    const coverageFeats = map.queryRenderedFeatures(e.point, { layers: coverageLayers });
    if (coverageFeats.length === 0) return;

    const ops = [...new Set(coverageFeats.map((f) => f.properties.operator))];
    const lines = ops.map((op) => {
        const info = OPERATORS[op];
        const dot = `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${info.color};margin-right:4px"></span>`;
        return `${dot}<b>${info.name}</b>`;
    });

    const quarter = coverageFeats[0].properties.quarter || "";
    const tech = coverageFeats[0].properties.technology || "";

    new maplibregl.Popup({ maxWidth: "250px" })
        .setLngLat(e.lngLat)
        .setHTML(
            `<div style="font-size:13px">` +
            `<div style="margin-bottom:4px;color:#666">${tech} — ${quarter}</div>` +
            lines.join("<br>") +
            `</div>`
        )
        .addTo(map);
});

// Curseur pointer
for (const op of Object.keys(OPERATORS)) {
    for (const layerPrefix of ["coverage-fill-", "antennas-"]) {
        map.on("mouseenter", `${layerPrefix}${op}`, () => {
            map.getCanvas().style.cursor = "pointer";
        });
        map.on("mouseleave", `${layerPrefix}${op}`, () => {
            map.getCanvas().style.cursor = "";
        });
    }
}

/**
 * Filtre les couches par opérateur.
 */
function filterByOperator(operator) {
    for (const op of Object.keys(OPERATORS)) {
        const visible = operator === "all" || operator === op;
        const vis = visible ? "visible" : "none";
        map.setLayoutProperty(`coverage-fill-${op}`, "visibility", vis);
        map.setLayoutProperty(`coverage-line-${op}`, "visibility", vis);
        map.setLayoutProperty(`antennas-${op}`, "visibility", vis);
    }
    updateLegend(operator);
}

/**
 * Construit la légende de la carte.
 */
function buildLegend() {
    const container = document.getElementById("map-legend");
    if (!container) return;

    for (const [op, info] of Object.entries(OPERATORS)) {
        const item = document.createElement("label");
        item.className = "legend-item";

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = true;
        checkbox.dataset.operator = op;
        checkbox.addEventListener("change", () => toggleOperator(op, checkbox.checked));

        const swatch = document.createElement("span");
        swatch.className = "legend-swatch";
        swatch.style.backgroundColor = info.color;

        const label = document.createElement("span");
        label.className = "legend-label";
        label.textContent = info.name;

        item.appendChild(checkbox);
        item.appendChild(swatch);
        item.appendChild(label);
        container.appendChild(item);
    }

    // Toggle antennes
    const sep = document.createElement("hr");
    sep.style.margin = "4px 0";
    sep.style.border = "none";
    sep.style.borderTop = "1px solid #e2e8f0";
    container.appendChild(sep);

    const antennaItem = document.createElement("label");
    antennaItem.className = "legend-item";

    const antennaCb = document.createElement("input");
    antennaCb.type = "checkbox";
    antennaCb.checked = true;
    antennaCb.addEventListener("change", () => {
        const vis = antennaCb.checked ? "visible" : "none";
        for (const op of Object.keys(OPERATORS)) {
            map.setLayoutProperty(`antennas-${op}`, "visibility", vis);
        }
    });

    const antennaSwatch = document.createElement("span");
    antennaSwatch.className = "legend-swatch";
    antennaSwatch.style.background = "radial-gradient(circle, #666 40%, transparent 40%)";
    antennaSwatch.style.border = "1px solid #999";

    const antennaLabel = document.createElement("span");
    antennaLabel.className = "legend-label";
    antennaLabel.textContent = "Antennes (z8+)";

    antennaItem.appendChild(antennaCb);
    antennaItem.appendChild(antennaSwatch);
    antennaItem.appendChild(antennaLabel);
    container.appendChild(antennaItem);
}

/**
 * Toggle la visibilité d'un opérateur via la légende.
 */
function toggleOperator(op, visible) {
    const vis = visible ? "visible" : "none";
    map.setLayoutProperty(`coverage-fill-${op}`, "visibility", vis);
    map.setLayoutProperty(`coverage-line-${op}`, "visibility", vis);
    map.setLayoutProperty(`antennas-${op}`, "visibility", vis);
}

/**
 * Synchronise la légende avec le filtre du select.
 */
function updateLegend(operator) {
    const checkboxes = document.querySelectorAll("#map-legend input[type=checkbox]");
    checkboxes.forEach((cb) => {
        if (cb.dataset.operator) {
            cb.checked = operator === "all" || cb.dataset.operator === operator;
        }
    });
}

// Construire la légende une fois la carte chargée
map.on("load", () => {
    buildLegend();
});
