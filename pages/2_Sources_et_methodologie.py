from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st


# ==========================================================
# WASH DATA OBSERVATORY
# Page secondaire : Sources & méthodologie
# ==========================================================

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_FILE = ROOT_DIR / "data" / "processed" / "wash_observatory.db"

st.set_page_config(
    page_title="Sources & méthodologie | WASH Data Observatory",
    page_icon="📚",
    layout="wide",
)


@st.cache_data
def load_database_tables():
    """Charge les tables sans modifier la base SQLite."""
    if not DB_FILE.exists():
        raise FileNotFoundError(
            f"Base SQLite introuvable : {DB_FILE}"
        )

    with sqlite3.connect(DB_FILE) as connection:
        observations = pd.read_sql_query(
            "SELECT * FROM observations", connection
        )
        indicators = pd.read_sql_query(
            "SELECT * FROM indicators", connection
        )

    return observations, indicators


st.title("📚 Sources & méthodologie")
st.caption(
    "Documentation de la provenance, des définitions et des limites "
    "des données du WASH Data Observatory."
)

try:
    observations, indicators = load_database_tables()
except Exception as error:
    st.error(f"Impossible de charger la base de données : {error}")
    st.stop()

required_columns = {"indicator_code", "value"}
missing_columns = required_columns.difference(observations.columns)

if missing_columns:
    st.error(
        "La table observations ne contient pas les colonnes attendues : "
        + ", ".join(sorted(missing_columns))
    )
    st.stop()

# Conversion en mémoire uniquement : la base SQLite n'est pas modifiée.
observations["value_numeric"] = pd.to_numeric(
    observations["value"], errors="coerce"
)

if "year" in observations.columns:
    observations["year_numeric"] = pd.to_numeric(
        observations["year"], errors="coerce"
    )
else:
    observations["year_numeric"] = pd.Series(
        pd.NA, index=observations.index, dtype="Float64"
    )

total_rows = len(observations)
available_values = int(observations["value_numeric"].notna().sum())
missing_values = total_rows - available_values
indicator_count = int(observations["indicator_code"].nunique())

valid_years = observations["year_numeric"].dropna()
period_text = (
    f"{int(valid_years.min())}–{int(valid_years.max())}"
    if not valid_years.empty
    else "Non renseignée"
)

country_text = "Non renseigné"
if "country" in observations.columns:
    countries = observations["country"].dropna().astype(str).unique().tolist()
    if countries:
        country_text = ", ".join(sorted(countries))

country_code_text = "Non renseigné"
if "country_iso3" in observations.columns:
    country_codes = (
        observations["country_iso3"].dropna().astype(str).unique().tolist()
    )
    if country_codes:
        country_code_text = ", ".join(sorted(country_codes))

source_text = "Non renseignée dans la table observations"
if "source" in observations.columns:
    sources = (
        observations["source"].dropna().astype(str).unique().tolist()
    )
    if sources:
        source_text = " ; ".join(sorted(sources))

# Dictionnaires de libellés issus des tables réellement présentes.
name_by_code = {}
if {"indicator_code", "indicator_name"}.issubset(indicators.columns):
    name_by_code = (
        indicators.dropna(subset=["indicator_code"])
        .drop_duplicates("indicator_code")
        .set_index("indicator_code")["indicator_name"]
        .to_dict()
    )

sdg_by_code = {}
if "sdg_indicator" in observations.columns:
    sdg_by_code = (
        observations.dropna(subset=["indicator_code"])
        .drop_duplicates("indicator_code")
        .set_index("indicator_code")["sdg_indicator"]
        .to_dict()
    )

# Ordre d'affichage stable : 6.1.1, 6.2.1a, 6.2.1b.
expected_order = [
    "SH.H2O.SMDW.ZS",
    "SH.STA.SMSS.ZS",
    "SH.STA.HYGN.ZS",
]

quality = (
    observations.groupby("indicator_code", dropna=False)
    .agg(
        total_observations=("indicator_code", "size"),
        valeurs_numeriques=("value_numeric", "count"),
    )
    .reset_index()
)

quality["valeurs_manquantes"] = (
    quality["total_observations"] - quality["valeurs_numeriques"]
)
quality["taux_completude_pct"] = (
    quality["valeurs_numeriques"]
    / quality["total_observations"]
    * 100
).round(1)
quality["indicateur_odd"] = quality["indicator_code"].map(sdg_by_code)
quality["nom_indicateur"] = quality["indicator_code"].map(name_by_code)

order_map = {code: position for position, code in enumerate(expected_order)}
quality["_ordre"] = quality["indicator_code"].map(order_map).fillna(999)
quality = quality.sort_values(["_ordre", "indicator_code"]).drop(
    columns="_ordre"
)

# ----------------------------------------------------------
# 1. Fiche d'identité du jeu de données
# ----------------------------------------------------------

st.header("1. Fiche d'identité du jeu de données")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Observations", f"{total_rows:,}".replace(",", " "))
k2.metric("Indicateurs", indicator_count)
k3.metric("Valeurs numériques", f"{available_values:,}".replace(",", " "))
k4.metric("Valeurs manquantes", f"{missing_values:,}".replace(",", " "))

identity_left, identity_right = st.columns(2)

with identity_left:
    st.markdown("**Périmètre géographique**")
    st.write(f"- Pays : {country_text}")
    st.write(f"- Code ISO3 : {country_code_text}")
    st.write(f"- Période présente dans la base : {period_text}")

with identity_right:
    st.markdown("**Informations techniques**")
    st.write("- Stockage : SQLite")
    st.write("- Fichier : `data/processed/wash_observatory.db`")
    st.write(f"- Source enregistrée dans les observations : {source_text}")
    st.write(
        "- Date exacte de récupération : non enregistrée dans la base actuelle."
    )

st.info(
    "La date de récupération n'est pas déduite de la date des observations. "
    "Elle devra être enregistrée explicitement par le pipeline lors d'une "
    "prochaine extraction."
)

st.divider()

# ----------------------------------------------------------
# 2. Sources des données
# ----------------------------------------------------------

st.header("2. Sources des données")

st.markdown(
    """
    **Source d'accès et de diffusion :** Banque mondiale, via les World
    Development Indicators (WDI) et l'Indicators API v2.

    **Producteur thématique indiqué dans les fiches des indicateurs :**
    Programme commun OMS/UNICEF de suivi de l'approvisionnement en eau,
    de l'assainissement et de l'hygiène (JMP).

    Il faut distinguer la plateforme qui diffuse les séries (Banque mondiale)
    du programme spécialisé auquel les fiches attribuent les données (JMP).
    """
)

source_col1, source_col2 = st.columns(2)

with source_col1:
    st.link_button(
        "Documentation officielle de l'API Banque mondiale",
        "https://datahelpdesk.worldbank.org/knowledgebase/articles/889392",
        use_container_width=True,
    )
    st.link_button(
        "Structure des appels API",
        "https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures",
        use_container_width=True,
    )

with source_col2:
    st.link_button(
        "Portail officiel OMS/UNICEF JMP",
        "https://washdata.org/",
        use_container_width=True,
    )
    st.link_button(
        "Méthodes d'estimation du JMP",
        "https://washdata.org/topics/methods/estimation-methods",
        use_container_width=True,
    )

st.caption(
    "Les fiches des indicateurs de la Banque mondiale affichent une "
    "attribution au WHO/UNICEF Joint Monitoring Programme et une licence "
    "CC BY 4.0. Vérifier les conditions applicables aux fichiers sources "
    "du JMP avant toute redistribution séparée."
)

st.divider()

# ----------------------------------------------------------
# 3. Dictionnaire des indicateurs
# ----------------------------------------------------------

st.header("3. Dictionnaire des trois indicateurs WASH")

indicator_definitions = pd.DataFrame(
    [
        {
            "ODD": "6.1.1",
            "Code Banque mondiale": "SH.H2O.SMDW.ZS",
            "Thème": "Eau potable",
            "Définition synthétique": (
                "Population utilisant un service d'eau potable géré en toute sécurité."
            ),
            "Critères JMP": (
                "Source améliorée, située sur place, disponible quand nécessaire "
                "et exempte de contamination fécale et chimique prioritaire."
            ),
        },
        {
            "ODD": "6.2.1a",
            "Code Banque mondiale": "SH.STA.SMSS.ZS",
            "Thème": "Assainissement",
            "Définition synthétique": (
                "Population utilisant un service d'assainissement géré en toute sécurité."
            ),
            "Critères JMP": (
                "Installation améliorée non partagée ; excreta traités et éliminés "
                "sur place en sécurité ou transportés puis traités hors site."
            ),
        },
        {
            "ODD": "6.2.1b",
            "Code Banque mondiale": "SH.STA.HYGN.ZS",
            "Thème": "Hygiène des mains",
            "Définition synthétique": (
                "Population disposant d'une installation de base pour le lavage des mains."
            ),
            "Critères JMP": (
                "Dispositif de lavage des mains avec eau et savon disponibles au domicile."
            ),
        },
    ]
)

st.dataframe(
    indicator_definitions,
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Les libellés courts ci-dessus sont des résumés pédagogiques. "
    "Consulter les définitions JMP officielles pour l'interprétation complète."
)

st.divider()

# ----------------------------------------------------------
# 4. Disponibilité et qualité des données
# ----------------------------------------------------------

st.header("4. Disponibilité et qualité des données")

quality_display = quality.rename(
    columns={
        "indicator_code": "Code",
        "indicateur_odd": "Indicateur ODD",
        "nom_indicateur": "Nom",
        "total_observations": "Observations",
        "valeurs_numeriques": "Valeurs numériques",
        "valeurs_manquantes": "Valeurs manquantes",
        "taux_completude_pct": "Complétude (%)",
    }
)

st.dataframe(
    quality_display,
    use_container_width=True,
    hide_index=True,
)

st.warning(
    "Pour l'indicateur d'assainissement (6.2.1a), 0 valeur numérique sur "
    "66 observations signifie que la valeur est indisponible dans cette "
    "extraction. Cela ne signifie absolument pas que 0 % de la population "
    "utilise un service d'assainissement géré en toute sécurité."
)

st.markdown(
    """
    **Règles de traitement appliquées dans le projet :**

    - Une valeur manquante reste manquante (`NULL` dans SQLite / `NaN` dans Pandas).
    - Une valeur manquante n'est jamais remplacée par zéro.
    - Les statistiques descriptives sont calculées uniquement sur les valeurs
      numériques disponibles.
    - Le taux de complétude est calculé comme :
      `valeurs numériques disponibles / nombre d'observations × 100`.
    - Les années sans valeur ne doivent pas être reliées artificiellement
      dans une courbe temporelle.
    """
)

st.divider()

# ----------------------------------------------------------
# 5. Limites d'interprétation
# ----------------------------------------------------------

st.header("5. Limites et précautions d'interprétation")

st.markdown(
    """
    1. **Disponibilité inégale :** les trois indicateurs n'ont pas le même
       niveau de complétude. Les comparaisons doivent tenir compte de cette
       différence.

    2. **Estimations et mesures :** les séries publiées par le JMP peuvent
       être construites à partir de plusieurs sources nationales et de
       méthodes d'estimation. Une valeur annuelle ne doit donc pas être
       automatiquement présentée comme une mesure directe réalisée cette
       année-là.

    3. **Absence de valeur :** l'absence d'une observation numérique ne
       prouve ni une absence de service ni une couverture nulle.

    4. **Traçabilité incomplète :** la base actuelle ne conserve pas encore
       de date d'extraction ni de version du jeu de données. Ces métadonnées
       devront être ajoutées au pipeline pour assurer la reproductibilité.

    5. **Périmètre :** les résultats décrivent les données présentes dans
       cette base pour le pays et les indicateurs sélectionnés. Ils ne
       remplacent pas une enquête nationale ni une validation auprès des
       institutions productrices.
    """
)

st.divider()

# ----------------------------------------------------------
# 6. Liens directs vers les fiches indicateurs
# ----------------------------------------------------------

st.header("6. Fiches officielles des indicateurs")

links = [
    (
        "ODD 6.1.1 – Eau potable gérée en toute sécurité",
        "https://data.worldbank.org/indicator/SH.H2O.SMDW.ZS",
    ),
    (
        "ODD 6.2.1a – Assainissement géré en toute sécurité",
        "https://data.worldbank.org/indicator/SH.STA.SMSS.ZS",
    ),
    (
        "ODD 6.2.1b – Installations de lavage des mains",
        "https://data.worldbank.org/indicator/SH.STA.HYGN.ZS",
    ),
]

for label, url in links:
    st.markdown(f"- [{label}]({url})")

st.caption(
    "WASH Data Observatory | Documentation des sources et de la méthodologie"
)
