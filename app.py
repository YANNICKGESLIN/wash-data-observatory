
from pathlib import Path
import sqlite3
import subprocess
import sys

import pandas as pd
import plotly.express as px
import streamlit as st


# ==========================================
# 1. CONFIGURATION
# ==========================================

ROOT_DIR = Path(__file__).resolve().parent

DB_FILE = ROOT_DIR / "data" / "processed" / "wash_observatory.db"

def ensure_database():

    if DB_FILE.exists():
        return

    rebuild_script = ROOT_DIR / "src" / "rebuild_database.py"

    if not rebuild_script.exists():
        raise FileNotFoundError(
            f"Script de reconstruction introuvable : {rebuild_script}"
        )

    st.info("Initialisation de la base de données WASH...")

    subprocess.run(
        [sys.executable, str(rebuild_script)],
        cwd=ROOT_DIR,
        check=True
    )

    if not DB_FILE.exists():
        raise FileNotFoundError(
            "La reconstruction n'a pas créé la base de données."
        )
    
st.set_page_config(
    page_title="WASH Data Observatory | Congo",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# st.markdown(
#     """
#     <style>
#         .stApp {
#             background: linear-gradient(135deg, #eef6ff 0%, #f8fbff 100%);
#         }
#     </style>
#     """,
#     unsafe_allow_html=True
# )

# Palette visuelle
BLUE = "#1677B8"
DARK_BLUE = "#12304A"
GREEN = "#22A06B"


# ==========================================
# 2. CHARGEMENT DES DONNEES
# ==========================================

@st.cache_data
def load_data():

    ensure_database()

    if not DB_FILE.exists():
        raise FileNotFoundError(
            f"Base de données introuvable : {DB_FILE}"
        )

    connection = sqlite3.connect(DB_FILE)

    query = """
        SELECT
            o.country,
            o.country_iso3,
            o.sdg_indicator,
            o.indicator_code,
            i.indicator_name,
            o.year,
            o.value,
            o.unit,
            o.source,
            o.original_source,
            o.source_url,
            o.retrieved_at,
            o.extraction_id,
            e.started_at AS extraction_started_at,
            e.completed_at AS extraction_completed_at,
            e.status AS extraction_status,
            e.observation_count AS extraction_observation_count,
            e.indicator_count AS extraction_indicator_count,
            e.notes AS extraction_notes
        FROM observations o
        JOIN indicators i
            ON o.indicator_code = i.indicator_code
        LEFT JOIN extraction_logs e
            ON o.extraction_id = e.extraction_id
        ORDER BY o.indicator_code, o.year
        """

    try:
        df = pd.read_sql_query(query, connection)
    finally:
        connection.close()

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    return df

def build_indicator_summary(data):

    summary = (
        data.groupby(
            ["indicator_code", "sdg_indicator", "indicator_name"],
            as_index=False,
            dropna=False
        )
        .agg(
            total_observations=("indicator_code", "size"),
            available_values=("value", "count")
        )
    )

    summary["missing_values"] = (
        summary["total_observations"]
        - summary["available_values"]
    )

    summary["completeness"] = (
        summary["available_values"]
        .div(summary["total_observations"].where(
            summary["total_observations"] > 0
        ))
        .mul(100)
        .fillna(0)
        .round(2)
    )

    return summary

try:
    df = load_data()

except Exception as error:
    st.error(f"Erreur de chargement des données : {error}")
    st.stop()


# ==========================================
# 3. EN-TETE
# ==========================================

st.title("💧 WASH DATA OBSERVATORY")

st.subheader(
    "Suivi des indicateurs Eau, Hygiène et Assainissement au Congo"
)

st.caption(
    "Plateforme de visualisation et d'exploration des données "
    "WASH | République du Congo"
)

st.divider()

# ==========================================
# 3B. PROVENANCE ET TRACABILITE
# ==========================================

st.header("🔎 Provenance et traçabilité des données")

if "extraction_id" in df.columns:

    extraction_info = (
        df.dropna(subset=["extraction_id"])
        .drop_duplicates(subset=["extraction_id"])
    )

    if not extraction_info.empty:

        extraction = extraction_info.iloc[0]

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Observations extraites",
            int(extraction["extraction_observation_count"])
        )

        col2.metric(
            "Indicateurs suivis",
            int(extraction["extraction_indicator_count"])
        )

        col3.metric(
            "Statut de l'extraction",
            str(extraction["extraction_status"])
        )

        st.markdown("**Sources des données**")

        source_col1, source_col2 = st.columns(2)

        with source_col1:
            st.info(
                f"**Source de diffusion**\n\n"
                f"{extraction['source']}"
            )

        with source_col2:
            st.info(
                f"**Source originale**\n\n"
                f"{extraction['original_source']}"
            )

        with st.expander("Consulter les détails de l'extraction"):

            st.write(
                "**Identifiant de l'extraction :**"
            )
            st.code(str(extraction["extraction_id"]))

            st.write(
                "**Début :**",
                extraction["extraction_started_at"]
            )

            st.write(
                "**Fin :**",
                extraction["extraction_completed_at"]
            )

            st.write(
                "**Note méthodologique :**",
                extraction["extraction_notes"]
            )

    else:
        st.warning(
            "Aucune information de traçabilité disponible."
        )

else:
    st.warning(
        "Les informations de traçabilité ne sont pas chargées."
    )

st.divider()

# ==========================================
# 4. BARRE LATERALE
# ==========================================

st.sidebar.title("⚙️ Navigation")

st.sidebar.markdown(
    "### Paramètres d'analyse"
)

indicators = (
    df[["indicator_code", "sdg_indicator", "indicator_name"]]
    .drop_duplicates()
    .sort_values("sdg_indicator")
)

indicator_options = {
    f"{row.sdg_indicator} | {row.indicator_name}": row.indicator_code
    for row in indicators.itertuples()
}

selected_label = st.sidebar.selectbox(
    "Sélectionner un indicateur",
    options=list(indicator_options.keys())
)

selected_code = indicator_options[selected_label]

selected_data = df[
    df["indicator_code"] == selected_code
].copy()

available_data = selected_data.dropna(
    subset=["value", "year"]
).copy()

st.sidebar.divider()

st.sidebar.markdown("### À propos")

st.sidebar.info(
    "Source principale : World Bank API. "
    "Les indicateurs sont associés aux métadonnées "
    "du programme OMS/UNICEF lorsque renseignées."
)



# ==========================================
# 5. VUE D'ENSEMBLE ET KPI
# ==========================================

st.header("📊 État du jeu de données")

total_observations = len(df)
available_values = df["value"].notna().sum()
missing_values = df["value"].isna().sum()

col1, col2, col3 = st.columns(3)

col1.metric("Observations", total_observations)
col2.metric("Valeurs disponibles", available_values)
col3.metric("Valeurs manquantes", missing_values)

st.divider()

st.subheader("Les 3 indicateurs WASH suivis")

indicator_summary = build_indicator_summary(df)

indicator_cards = st.columns(3)

for col, (_, row) in zip(
    indicator_cards,
    indicator_summary.iterrows()
):
    with col:
        st.metric(
            label=f"ODD {row['sdg_indicator']}",
            value=(
                f"{int(row['available_values'])}"
                f"/{int(row['total_observations'])}"
            ),
            delta=f"{row['completeness']:.1f}% de complétude"
        )

        st.caption(row["indicator_name"])

st.divider()


# ==========================================
# 6. ANALYSE DE L'INDICATEUR
# ==========================================

st.header("🔎 Analyse de l'indicateur sélectionné")
st.markdown(f"**{selected_label}**")

# Conserver toutes les années, même celles sans valeur
min_year = int(selected_data["year"].min())
max_year = int(selected_data["year"].max())

year_range = st.slider(
    "Période d'analyse",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

filtered_data = selected_data[
    selected_data["year"].between(
        year_range[0],
        year_range[1]
    )
].copy().sort_values("year")

# Séparer les observations disponibles pour les statistiques
observed_data = filtered_data.dropna(
    subset=["value"]
).copy()

if observed_data.empty:

    st.warning(
        "Aucune valeur numérique disponible pour cet indicateur "
        "dans la période sélectionnée."
    )

    st.info(
        "Les années sont conservées dans la base, mais les valeurs "
        "manquantes ne peuvent pas être interprétées comme des zéros."
    )

else:

    # Statistiques descriptives
    mean_value = observed_data["value"].mean()
    min_value = observed_data["value"].min()
    max_value = observed_data["value"].max()

    first_value = observed_data.iloc[0]["value"]
    last_value = observed_data.iloc[-1]["value"]

    first_year = int(observed_data.iloc[0]["year"])
    last_year = int(observed_data.iloc[-1]["year"])

    variation = last_value - first_value

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    kpi1.metric("Moyenne", f"{mean_value:.2f} %")
    kpi2.metric("Minimum", f"{min_value:.2f} %")
    kpi3.metric("Maximum", f"{max_value:.2f} %")
    kpi4.metric("Variation", f"{variation:+.2f} pp")

    st.caption(
        f"Première observation disponible : {first_year} | "
        f"Dernière observation disponible : {last_year}"
    )

    # Années réellement disponibles
    observed_years = sorted(
        observed_data["year"].astype(int).tolist()
    )

    st.markdown("**Années disposant de valeurs :**")

    st.write(", ".join(map(str, observed_years)))

    st.divider()

    # Graphique temporel : conserver les valeurs manquantes
    st.subheader("📈 Évolution temporelle")

    fig = px.line(
        filtered_data,
        x="year",
        y="value",
        markers=True,
        title="Évolution de l'indicateur",
        labels={
            "year": "Année",
            "value": "Population (%)"
        },
        template="plotly_white"
    )

    fig.update_traces(
        line=dict(color="#1677B8", width=3),
        marker=dict(size=8),
        connectgaps=False
    )

    fig.update_layout(
        xaxis_title="Année",
        yaxis_title="Population (%)",
        hovermode="x unified"
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )

    st.info(
        "Les interruptions de la courbe correspondent aux années "
        "sans valeur numérique disponible. Elles ne représentent "
        "pas une valeur de zéro."
    )

    # Tableau de toutes les années de la période
    st.subheader("📋 Données de la période sélectionnée")

    display_data = filtered_data[
        ["year", "indicator_code", "indicator_name", "value"]
    ].copy()

    display_data["statut"] = display_data["value"].apply(
        lambda x: "Disponible" if pd.notna(x) else "Manquante"
    )

    display_data = display_data.rename(
        columns={
            "year": "Année",
            "indicator_code": "Code",
            "indicator_name": "Indicateur",
            "value": "Valeur (%)",
            "statut": "Statut"
        }
    )

    st.dataframe(
        display_data,
        width="stretch",
        hide_index=True
    )

    csv_data = display_data.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="⬇️ Télécharger les données CSV",
        data=csv_data,
        file_name="congo_wash_analysis.csv",
        mime="text/csv"
    )

    st.warning(
        "Attention méthodologique : la régularité de certaines "
        "séries temporelles mérite une vérification de la méthode "
        "de production des estimations avant de les interpréter "
        "comme des mesures annuelles directes."
    )


# ==========================================
# 7. QUALITE DES DONNEES
# ==========================================

st.divider()

st.header("🧪 Qualité et disponibilité des données")

quality = indicator_summary.copy()

st.dataframe(
    quality.rename(
        columns={
            "indicator_code": "Code",
            "sdg_indicator": "ODD",
            "indicator_name": "Indicateur",
            "total_observations": "Observations",
            "available_values": "Valeurs disponibles",
            "missing_values": "Valeurs manquantes",
            "completeness": "Complétude (%)"
        }
    ),
    width="stretch",
    hide_index=True
)

fig_quality = px.bar(
    quality,
    x="sdg_indicator",
    y="completeness",
    color="sdg_indicator",
    text="completeness",
    title="Taux de complétude par indicateur",
    labels={
        "sdg_indicator": "Indicateur ODD",
        "completeness": "Complétude (%)"
    },
    template="plotly_white"
)

fig_quality.update_traces(
    texttemplate="%{text:.1f}%",
    textposition="outside"
)

fig_quality.update_layout(
    showlegend=False,
    yaxis=dict(range=[0, 110])
)

st.plotly_chart(
    fig_quality,
    width="stretch"
)


# ==========================================
# 7B. QUALITY MONITOR - CONTROLES AUTOMATIQUES
# ==========================================

st.divider()

st.header("🛡️ Quality Monitor")
st.caption(
    "Contrôles automatiques de cohérence, d'intégrité "
    "et de traçabilité du jeu de données."
)

# 1. Détection des doublons
duplicate_count = df.duplicated(
    subset=["country_iso3", "indicator_code", "year"]
).sum()

# 2. Détection des valeurs hors intervalle 0-100
valid_values = df["value"].dropna()

out_of_range_count = (
    (~valid_values.between(0, 100)).sum()
)

# 3. Vérification des métadonnées
metadata_columns = [
    "country_iso3",
    "indicator_code",
    "indicator_name",
    "source",
    "original_source",
    "source_url",
    "retrieved_at"
]

available_metadata = [
    col for col in metadata_columns if col in df.columns
]

missing_metadata_count = (
    df[available_metadata].isna().any(axis=1).sum()
)

# 4. Vérification de la traçabilité

if "extraction_id" in df.columns:

    missing_extraction_id = (
        df["extraction_id"].isna()
        | df["extraction_id"].astype(str).str.strip().eq("")
    ).sum()

else:
    missing_extraction_id = len(df)


if (
    "extraction_id" in df.columns
    and "extraction_started_at" in df.columns
):

    valid_extraction_id = (
        df["extraction_id"].notna()
        & df["extraction_id"].astype(str).str.strip().ne("")
    )

    orphan_extraction_count = (
        valid_extraction_id
        & df["extraction_started_at"].isna()
    ).sum()

else:
    orphan_extraction_count = len(df)

# 5. Vérification des années
missing_year_count = df["year"].isna().sum()

# Tableau de contrôle
checks = [
    ("Doublons", duplicate_count),
    ("Valeurs hors intervalle 0-100", out_of_range_count),
    ("Observations avec métadonnées manquantes", missing_metadata_count),
    ("Observations sans identifiant d'extraction", missing_extraction_id),
    ("Observations liées à une extraction inexistante", orphan_extraction_count),
    ("Observations sans année", missing_year_count)
]

quality_checks = pd.DataFrame(
    checks,
    columns=["Contrôle", "Anomalies détectées"]
)

quality_checks["Résultat"] = quality_checks[
    "Anomalies détectées"
].apply(
    lambda x: "Conforme" if x == 0 else "À vérifier"
)

# Indicateurs de synthèse
qc1, qc2, qc3 = st.columns(3)

qc1.metric(
    "Contrôles réalisés",
    len(quality_checks)
)

qc2.metric(
    "Anomalies détectées",
    int(quality_checks["Anomalies détectées"].sum())
)

qc3.metric(
    "Observations analysées",
    len(df)
)

# Résultats détaillés
st.subheader("Résultats des contrôles")

st.dataframe(
    quality_checks,
    width='stretch',
    hide_index=True
)

if quality_checks["Anomalies détectées"].sum() == 0:
    st.success(
        "Tous les contrôles automatiques sont conformes."
    )
else:
    st.warning(
        "Certaines anomalies nécessitent une vérification."
    )

st.info(
    "Important : les valeurs manquantes des indicateurs "
    "ne sont pas considérées automatiquement comme des erreurs. "
    "Elles sont suivies séparément dans le tableau de complétude."
)


# ==========================================
# 8. PIED DE PAGE
# ==========================================

st.divider()

st.caption(
    "WASH Data Observatory | Congo |\n"
    "Projet de portfolio en Data Science et Santé Publique.\n"
    "DATAFREEK Consulting || 2026 "
    "Tout Droits réservés."
)

st.caption(
    "Les valeurs manquantes ne sont pas remplacées par zéro. "
    "Les résultats doivent être interprétés selon la période "
    "et la méthodologie de production des données."
)

