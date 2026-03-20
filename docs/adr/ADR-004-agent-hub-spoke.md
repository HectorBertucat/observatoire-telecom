# ADR-004 : Architecture hub-and-spoke pour l'agent d'analyse

## Statut : Accepté (mars 2026)

## Contexte
Le projet inclut un agent IA capable d'analyser les données télécom et de
produire des rapports structurés. L'analyse implique plusieurs étapes :
récupération des données, analyse/comparaison, génération de rapport.

## Décision
Adopter une architecture **hub-and-spoke** avec un agent coordinateur (hub) et
3 sous-agents spécialisés (spokes) via **pydantic-ai**.

```
Coordinateur (hub)
├── Fetcher (spoke) → récupère les données
├── Analyzer (spoke) → compare, identifie les insights
└── Reporter (spoke) → génère le rapport structuré
```

## Options considérées

| Pattern | Avantages | Inconvénients |
|---------|-----------|---------------|
| Agent unique monolithique | Simple | Prompt trop long, pas modulaire |
| Pipeline linéaire | Prévisible | Pas de retry/fallback partiel |
| Hub-and-spoke | Modulaire, retry par spoke | Plus complexe à orchestrer |
| Réseau d'agents (mesh) | Très flexible | Overkill pour 3 tâches |

## Conséquences
- **Positif** : chaque sous-agent a un prompt court et ciblé
- **Positif** : le coordinateur peut retry un spoke en cas d'échec sans relancer tout
- **Positif** : sortie structurée (AnalysisReport Pydantic) validée automatiquement
- **Négatif** : 4 appels API Claude au lieu d'1 (coût + latence)
- **Note CCA-F** : le pattern hub-and-spoke est un classique du domaine 1 de l'examen
  (27% — Agentic Architecture & Orchestration)
