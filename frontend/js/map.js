/* Initialisation et gestion de la carte Leaflet */

const map = L.map("map").setView([46.603, 2.888], 6);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 18,
}).addTo(map);

const MAP_OPERATOR_COLORS = {
    OF: "#FF6600",
    SFR: "#E4002B",
    BYT: "#003DA5",
    FREE: "#CD1719",
};

const MAP_OPERATOR_NAMES = {
    OF: "Orange",
    SFR: "SFR",
    BYT: "Bouygues",
    FREE: "Free",
};

let coverageLayers = {};

/**
 * Charge et affiche les polygones de couverture pour un opérateur.
 */
async function loadCoverageLayer(operator, technology) {
    if (coverageLayers[operator]) {
        map.removeLayer(coverageLayers[operator]);
    }

    try {
        const response = await fetch(
            `/api/v1/coverage/geojson?operator=${operator}&technology=${technology}`
        );
        const geojson = await response.json();

        if (geojson.features.length === 0) return;

        const color = MAP_OPERATOR_COLORS[operator] || "#999";
        const name = MAP_OPERATOR_NAMES[operator] || operator;

        coverageLayers[operator] = L.geoJSON(geojson, {
            style: {
                color: color,
                weight: 0.8,
                fillColor: color,
                fillOpacity: 0.35,
            },
            onEachFeature: function (feature, layer) {
                const props = feature.properties;
                layer.bindPopup(
                    `<b>${name}</b><br>${props.technology} — ${props.quarter}`
                );
            },
        }).addTo(map);
    } catch (error) {
        console.error(`Erreur chargement couverture ${operator}:`, error);
    }
}

/**
 * Supprime toutes les couches de couverture.
 */
function clearCoverageLayers() {
    for (const key of Object.keys(coverageLayers)) {
        map.removeLayer(coverageLayers[key]);
    }
    coverageLayers = {};
}
