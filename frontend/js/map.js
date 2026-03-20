/* Initialisation et gestion de la carte Leaflet */

// Carte centrée sur la France métropolitaine
const map = L.map("map").setView([46.603, 2.888], 6);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 18,
}).addTo(map);

// Couche GeoJSON pour les données de couverture
let coverageLayer = null;

/**
 * Charge et affiche les données GeoJSON de couverture sur la carte.
 */
function updateMap(department) {
    if (!department) return;

    // Coordonnées approximatives des chefs-lieux de département
    const deptCenters = {
        "13": [43.3, 5.4],
        "31": [43.6, 1.44],
        "33": [44.84, -0.58],
        "69": [45.76, 4.84],
        "75": [48.86, 2.35],
    };

    const center = deptCenters[department] || [46.603, 2.888];
    map.setView(center, 9);

    // Supprimer l'ancienne couche si existante
    if (coverageLayer) {
        map.removeLayer(coverageLayer);
    }
}
