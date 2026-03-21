# Roadmap — Observatoire Telecom France

## Fait (v0.1)

- [x] Pipeline ARCEP couverture 2G/3G/4G (2724 polygones)
- [x] Pipeline ANFR antennes (354k sites, 2G-5G)
- [x] Referentiel communes INSEE (34 955)
- [x] mart_coverage_by_commune (197k lignes)
- [x] API REST FastAPI (14 endpoints)
- [x] Serveur MCP (5 tools)
- [x] Agent Claude hub-and-spoke (teste avec TestModel)
- [x] Carte MapLibre + PMTiles (couverture + antennes + 5G halos)
- [x] Dark mode dashboard, 3 charts, filtres techno/operateur/departement
- [x] Recherche commune + nearby (clic droit)
- [x] Export CSV
- [x] CI/CD GitHub Actions + mypy strict
- [x] Documentation (CHANGELOG, 4 ADR, data dictionary, README)

## Phase 2 — Trajets SNCF + couverture le long des lignes

### Donnees source

**Traces des lignes ferroviaires (RFN)**
- Source : SNCF Open Data
- URL : https://ressources.data.sncf.com/explore/dataset/formes-des-lignes-du-rfn/
- Format : GeoJSON (8.8 MB) ou Shapefile (3.1 MB)
- Licence : ODbL
- Contenu : toutes les lignes du Reseau Ferre National, precision decametrique

### Architecture prevue

```
1. Telecharger le GeoJSON des lignes RFN
2. Charger dans DuckDB (table ref_railway_lines)
3. API : POST /api/v1/routes/coverage
   Input : { line_id ou [depart_coords, arrivee_coords] }
   Algo : buffer 2km autour du trace -> intersection avec raw_coverage
   Output : % couvert par operateur + classement
4. Frontend : panneau "Trajet", input depart/arrivee (autocomplete gares),
   trace sur la carte + resultats couverture
5. MCP tool : analyze_route_coverage(line_id)
```

### Etapes

- [ ] Telecharger + charger les lignes RFN dans DuckDB
- [ ] Telecharger les gares (pour autocomplete depart/arrivee)
- [ ] API endpoint couverture le long d'une ligne
- [ ] Frontend panneau trajet
- [ ] Tests

## Phase 3 — Donnees de couverture reelle (crowdsourced)

### Sources identifiees

| Source | Open | Format | Taille | Contenu |
|--------|------|--------|--------|---------|
| **ARCEP crowdsourcing** | Oui (ODbL) | CSV | ~50 MB | Mesures terrain (debit, RSRP, RSRQ) |
| **Ookla Speedtest** | Oui (AWS) | Parquet/Shapefile | ~300 MB/trimestre | Debit moyen par tuile 600m |
| **OpenCelliD** | Oui (CC-BY-SA) | CSV | ~900 MB gz | Positions cell towers crowdsourcees |
| **nPerf** | Non (commercial) | — | — | Couverture + debit temps reel |

### Recommandation : ARCEP crowdsourcing + Ookla

- **ARCEP crowdsourcing** : mesures reelles de qualite de service, meme portail que la couverture
  - URL : https://data.arcep.fr/mobile/mesures_crowdsourcing/
  - Champs : debit, RSRP, RSRQ, operateur, techno, coordonnees GPS
  - Utilite : comparer couverture theorique vs reelle

- **Ookla Speedtest** : debits par tuile de 600m, couvre toute la France
  - URL : https://github.com/teamookla/ookla-open-data
  - Trimestres disponibles : Q1 2019 — Q4 2025
  - Utilite : carte de debit reel overlay sur la couverture theorique

### Architecture prevue

```
1. Telecharger les CSV crowdsourcing ARCEP (dernier trimestre)
2. Telecharger les tuiles Ookla Speedtest (dernier trimestre, mobile)
3. Charger dans DuckDB :
   - raw_crowdsourcing (mesures ARCEP)
   - raw_speedtest_tiles (tuiles Ookla)
4. API : GET /api/v1/quality/commune/{code} (debit moyen par operateur)
5. Frontend : toggle "Couverture theorique / reelle"
6. Carte : heatmap de debit (tuiles Ookla coloriees par debit)
```

### Etapes

- [ ] Telecharger et explorer les CSV crowdsourcing ARCEP
- [ ] Telecharger les tuiles Ookla (Parquet, filtre France)
- [ ] Charger dans DuckDB
- [ ] API qualite de service
- [ ] Frontend toggle theorique/reel
- [ ] Generer des tuiles heatmap de debit

## Phase 4 — Ameliorations UX

- [ ] Comparaison cote-a-cote de 2 operateurs (split view)
- [ ] Mode sombre/clair toggle
- [ ] PWA (Progressive Web App) pour mobile
- [ ] Recherche par nom de ville (pas seulement code INSEE)
- [ ] Docker build + deploiement Proxmox
- [ ] Agent Claude E2E avec vraie API key
