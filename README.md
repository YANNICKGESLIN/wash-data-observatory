# 💧 WASH Data Observatory | Congo

**Observatoire des données sur l'eau, l'hygiène et l'assainissement en République du Congo**

[![Python](https://img.shields.io/badge/Python-3.14-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Framework-Streamlit-red)](https://streamlit.io/)
[![Data](https://img.shields.io/badge/Data-WASH-1677B8)]()
[![Status](https://img.shields.io/badge/Status-In%20Development-orange)]()

## 1. Présentation du projet

Le **WASH Data Observatory** est une application de visualisation et d'exploration des données relatives à l'eau potable, à l'hygiène et à l'assainissement (WASH) en République du Congo.

Ce projet vise à centraliser, structurer et analyser des indicateurs publics afin de faciliter leur consultation et de contribuer au suivi des Objectifs de développement durable (ODD), notamment l'ODD 6 : garantir l'accès de tous à l'eau et à l'assainissement.

Il constitue également un projet de portfolio associant Data Science, analyse de données et santé publique.

## 2. Objectifs

### Objectif général

Développer une plateforme interactive de suivi et d'exploration des indicateurs WASH en République du Congo à partir de données publiques.

### Objectifs spécifiques

- Collecter et structurer les données publiques relatives aux indicateurs WASH.
- Concevoir une base de données relationnelle avec SQLite.
- Mesurer la disponibilité et la complétude des observations.
- Visualiser les évolutions temporelles des indicateurs.
- Mettre en place des contrôles automatiques de qualité.
- Assurer la traçabilité des extractions de données.

## 3. Indicateurs suivis

Le projet suit trois indicateurs associés à l'ODD 6.

| ODD | Indicateur | Code World Bank |
|---|---|---|
| 6.1.1 | Services d'eau potable gérés en toute sécurité | SH.H2O.SMDW.ZS |
| 6.2.1b | Installations de base pour le lavage des mains | SH.STA.HYGN.ZS |
| 6.2.1a | Services d'assainissement gérés en toute sécurité | SH.STA.SMSS.ZS |

Les indicateurs sont exprimés en pourcentage de la population.

## 4. Sources des données

**Source de diffusion :**
- Banque mondiale, base World Development Indicators (WDI).
- API : https://api.worldbank.org/

**Source originale :**
- Programme commun OMS/UNICEF de suivi de l'approvisionnement en eau, de l'assainissement et de l'hygiène (JMP).

Les données sont récupérées à partir des identifiants des indicateurs et du code pays `COG`.

## 5. État actuel du jeu de données

La base de données comporte 198 observations réparties sur trois indicateurs.

| Indicateur | Observations | Disponibles | Manquantes |
|---|---:|---:|---:|
| Eau potable | 66 | 22 | 44 |
| Hygiène des mains | 66 | 9 | 57 |
| Assainissement | 66 | 0 | 66 |
| **Total** | **198** | **31** | **167** |

**Complétude globale : 15,66 %.**

Ces résultats décrivent la disponibilité des valeurs dans la base actuelle. Ils ne constituent pas une mesure directe de la performance nationale en matière de WASH.

Les valeurs manquantes sont conservées comme valeurs nulles (`NULL` dans SQLite et `NaN` dans Pandas). Elles ne sont jamais remplacées automatiquement par zéro.

## 6. Architecture technique

| Composant | Technologie | Fonction |
|---|---|---|
| Langage | Python | Traitement et analyse |
| Interface | Streamlit | Dashboard interactif |
| Analyse | Pandas | Manipulation des données |
| Visualisation | Plotly | Graphiques interactifs |
| Stockage | SQLite | Base de données relationnelle |
| Extraction | API World Bank | Accès aux données publiques |

### Structure du projet

```text
wash-data-observatory/
│
├── app.py
│
├── data/
│   ├── raw/
│   │   └── congo_wash_all_years.csv
│   │
│   └── processed/
│       ├── wash_observatory.db
│       └── wash_observatory_backup_20261112.db
│
├── src/
│   └── migrate_extraction_logs.py
│
├── .venv/
│
└── README.md
```

Cette structure présente les principaux éléments connus du projet. Elle pourra être complétée avec les autres scripts et fichiers de configuration.

## 7. Fonctionnalités du dashboard

### Vue d'ensemble
- Nombre total d'observations.
- Nombre de valeurs disponibles.
- Nombre de valeurs manquantes.
- Complétude par indicateur.

### Analyse des indicateurs
- Sélection individuelle des indicateurs.
- Filtrage par période.
- Statistiques descriptives.
- Visualisation des séries temporelles.
- Consultation des observations.
- Export des données au format CSV.

### Provenance et traçabilité
- Identification des sources de diffusion et des sources originales.
- Identifiant unique de l'extraction.
- Dates de début et de fin.
- Nombre d'observations et d'indicateurs associés.

### Quality Monitor
- Détection des doublons.
- Contrôle des valeurs hors intervalle 0–100.
- Vérification des métadonnées.
- Contrôle des identifiants d'extraction.
- Vérification des années manquantes.

## 8. Installation et exécution

### Prérequis

- Python installé.
- Git (facultatif).
- Visual Studio Code (facultatif).

### Installation sous Windows PowerShell

Cloner le dépôt si le projet est hébergé sur GitHub :

```powershell
git clone URL_DU_DEPOT
cd wash-data-observatory
```

Créer un environnement virtuel :

```powershell
python -m venv .venv
```

Activer l'environnement :

```powershell
.\.venv\Scripts\Activate.ps1
```

Installer les dépendances :

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Reconstruire la base de données :

```powershell
python src/rebuild_database.py
```

Lancer l'application :

```powershell
streamlit run app.py
```

L'application est ensuite accessible depuis le navigateur à l'adresse locale indiquée par Streamlit.

## 9. Contrôles de qualité et intégrité

Les contrôles actuellement réalisés sur la base ont donné les résultats suivants :

- 198 observations enregistrées.
- 198 observations rattachées à une extraction.
- Une extraction historique documentée.
- Trois indicateurs suivis.
- Aucun doublon détecté lors du dernier audit.
- Aucune valeur numérique hors de l'intervalle 0–100 lors du dernier audit.
- Aucune métadonnée obligatoire manquante lors du dernier audit.

Ces résultats correspondent à l'état de la base lors du contrôle et devront être actualisés après chaque nouvelle extraction.

## 10. Limites méthodologiques

Plusieurs précautions sont nécessaires pour interpréter les résultats :

1. La disponibilité des données varie selon les indicateurs.
2. L'indicateur d'assainissement ne présente actuellement aucune valeur numérique dans la base.
3. Les valeurs manquantes ne doivent pas être interprétées comme des zéros.
4. La régularité des années présentes dans la base ne garantit pas que chaque observation représente une mesure annuelle directe.
5. Les méthodes de production des estimations doivent être vérifiées auprès des sources originales avant toute interprétation approfondie des tendances.

Le projet repose actuellement sur des données publiques et ne prétend pas remplacer une enquête de terrain ou une validation institutionnelle.

## 11. Perspectives d'évolution

Les prochaines améliorations envisagées sont :

- Automatisation et historisation des extractions.
- Renforcement des contrôles de qualité.
- Amélioration de l'ergonomie et de l'expérience utilisateur.
- Documentation détaillée du dictionnaire de données.
- Déploiement de l'application en ligne.
- Intégration éventuelle de nouvelles sources publiques vérifiées.

## 12. Auteur et contexte

**WASH Data Observatory | Congo**

Projet de portfolio en Data Science et santé publique.

Domaines d'application :
- Santé publique.
- Eau, hygiène et assainissement.
- Analyse et visualisation des données.
- Suivi des indicateurs des ODD.

**Technologies : Python | Pandas | SQLite | Plotly | Streamlit**

---

*Projet en développement. Les données, les méthodes et les fonctionnalités sont susceptibles d'évoluer au fil des travaux.*