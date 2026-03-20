/* Carte MapLibre GL JS avec vector tiles PMTiles */

// Enregistrer le protocole PMTiles
const protocol = new pmtiles.Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);

const OPERATOR_COLORS = {
    OF: "#FF6600",
    SFR: "#E4002B",
    BYT: "#003DA5",
    FREE: "#CD1719",
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
            // Une couche fill par opérateur pour pouvoir filtrer
            ...Object.entries(OPERATOR_COLORS).map(([op, color]) => ({
                id: `coverage-fill-${op}`,
                type: "fill",
                source: "coverage",
                "source-layer": "coverage",
                filter: ["==", ["get", "operator"], op],
                paint: {
                    "fill-color": color,
                    "fill-opacity": 0.35,
                },
            })),
            ...Object.entries(OPERATOR_COLORS).map(([op, color]) => ({
                id: `coverage-line-${op}`,
                type: "line",
                source: "coverage",
                "source-layer": "coverage",
                filter: ["==", ["get", "operator"], op],
                paint: {
                    "line-color": color,
                    "line-width": 0.5,
                    "line-opacity": 0.6,
                },
            })),
        ],
    },
    center: [2.888, 46.603],
    zoom: 5.5,
    maxZoom: 14,
});

// Popup au clic
map.on("click", (e) => {
    // Chercher dans toutes les couches coverage-fill-*
    const layers = Object.keys(OPERATOR_COLORS).map((op) => `coverage-fill-${op}`);
    const features = map.queryRenderedFeatures(e.point, { layers });

    if (features.length === 0) return;

    const props = features[0].properties;
    const opName = {
        OF: "Orange",
        SFR: "SFR",
        BYT: "Bouygues Telecom",
        FREE: "Free Mobile",
    };

    new maplibregl.Popup()
        .setLngLat(e.lngLat)
        .setHTML(
            `<b>${opName[props.operator] || props.operator}</b><br>` +
                `${props.technology} — ${props.quarter}`
        )
        .addTo(map);
});

// Curseur pointer au survol
const allFillLayers = Object.keys(OPERATOR_COLORS).map((op) => `coverage-fill-${op}`);
map.on("mouseenter", allFillLayers[0], () => (map.getCanvas().style.cursor = "pointer"));
map.on("mouseleave", allFillLayers[0], () => (map.getCanvas().style.cursor = ""));

/**
 * Filtre les couches par opérateur.
 */
function filterByOperator(operator) {
    for (const op of Object.keys(OPERATOR_COLORS)) {
        const visible = operator === "all" || operator === op;
        map.setLayoutProperty(`coverage-fill-${op}`, "visibility", visible ? "visible" : "none");
        map.setLayoutProperty(`coverage-line-${op}`, "visibility", visible ? "visible" : "none");
    }
}
