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
        },
        layers: [
            {
                id: "osm-tiles",
                type: "raster",
                source: "osm",
                minzoom: 0,
                maxzoom: 19,
            },
            // Fill + line par opérateur
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
        ],
    },
    center: [2.888, 46.603],
    zoom: 5.5,
    maxZoom: 14,
});

// Navigation controls
map.addControl(new maplibregl.NavigationControl(), "top-right");

// Popup au clic
map.on("click", (e) => {
    const layers = Object.keys(OPERATORS).map((op) => `coverage-fill-${op}`);
    const features = map.queryRenderedFeatures(e.point, { layers });
    if (features.length === 0) return;

    // Lister tous les opérateurs à ce point
    const ops = [...new Set(features.map((f) => f.properties.operator))];
    const lines = ops.map((op) => {
        const info = OPERATORS[op];
        const dot = `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${info.color};margin-right:4px"></span>`;
        return `${dot}<b>${info.name}</b>`;
    });

    const quarter = features[0].properties.quarter || "";
    const tech = features[0].properties.technology || "";

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
    map.on("mouseenter", `coverage-fill-${op}`, () => {
        map.getCanvas().style.cursor = "pointer";
    });
    map.on("mouseleave", `coverage-fill-${op}`, () => {
        map.getCanvas().style.cursor = "";
    });
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
}

/**
 * Toggle la visibilité d'un opérateur via la légende.
 */
function toggleOperator(op, visible) {
    const vis = visible ? "visible" : "none";
    map.setLayoutProperty(`coverage-fill-${op}`, "visibility", vis);
    map.setLayoutProperty(`coverage-line-${op}`, "visibility", vis);
}

/**
 * Synchronise la légende avec le filtre du select.
 */
function updateLegend(operator) {
    const checkboxes = document.querySelectorAll("#map-legend input[type=checkbox]");
    checkboxes.forEach((cb) => {
        cb.checked = operator === "all" || cb.dataset.operator === operator;
    });
}

// Construire la légende une fois la carte chargée
map.on("load", () => {
    buildLegend();
});
