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

let coverageLayers = {};

/**
 * Charge et affiche les enveloppes de couverture pour un opérateur.
 */
async function loadCoverageLayer(operator, technology) {
    if (coverageLayers[operator]) {
        map.removeLayer(coverageLayers[operator]);
    }

    try {
        const response = await fetch(
            `/api/v1/coverage/geojson?operator=${operator}&technology=${technology}&limit=50`
        );
        const geojson = await response.json();

        if (geojson.features.length === 0) return;

        const color = MAP_OPERATOR_COLORS[operator] || "#999";

        coverageLayers[operator] = L.geoJSON(geojson, {
            style: {
                color: color,
                weight: 1.5,
                fillColor: color,
                fillOpacity: 0.25,
            },
            onEachFeature: function (feature, layer) {
                const props = feature.properties;
                const pts = props.detail_points
                    ? props.detail_points.toLocaleString("fr-FR")
                    : "?";
                layer.bindPopup(
                    `<b>${props.operator}</b> (${props.technology})<br>` +
                        `Trimestre: ${props.quarter}<br>` +
                        `Détail: ${pts} points`
                );
            },
        }).addTo(map);

        map.fitBounds(coverageLayers[operator].getBounds(), { padding: [20, 20] });
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
