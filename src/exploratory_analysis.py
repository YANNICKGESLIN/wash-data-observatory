
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# 1. CONFIGURATION
# ==========================================

ROOT_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    ROOT_DIR / "data/processed/congo_wash_analysis_ready.csv"
)

REPORT_DIR = ROOT_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

print("\n==========================================")
print(" WASH DATA OBSERVATORY")
print(" EXPLORATORY DATA ANALYSIS")
print("==========================================")

# ==========================================
# 2. CHARGEMENT DES DONNEES
# ==========================================

df = pd.read_csv(INPUT_FILE)

df["year"] = pd.to_numeric(df["year"])
df["value"] = pd.to_numeric(df["value"])

print(f"\nObservations analysées : {len(df)}")
print(f"Indicateurs étudiés : {df['indicator_code'].nunique()}")

# ==========================================
# 3. STATISTIQUES DESCRIPTIVES
# ==========================================

statistics = (
    df.groupby(["indicator_code", "sdg_indicator", "indicator_name"])
    .agg(
        observations=("value", "count"),
        moyenne=("value", "mean"),
        mediane=("value", "median"),
        minimum=("value", "min"),
        maximum=("value", "max"),
        ecart_type=("value", "std"),
        premiere_annee=("year", "min"),
        derniere_annee=("year", "max")
    )
    .reset_index()
)

numeric_columns = [
    "moyenne", "mediane", "minimum",
    "maximum", "ecart_type"
]

statistics[numeric_columns] = (
    statistics[numeric_columns].round(2)
)

print("\n--- STATISTIQUES DESCRIPTIVES ---\n")
print(statistics.to_string(index=False))

statistics.to_csv(
    REPORT_DIR / "descriptive_statistics.csv",
    index=False
)

# ==========================================
# 4. EVOLUTION TEMPORELLE
# ==========================================

print("\n--- DONNEES PAR ANNEE ---\n")

temporal_data = df.sort_values(
    ["indicator_code", "year"]
)

print(
    temporal_data[
        ["indicator_code", "year", "value"]
    ].to_string(index=False)
)

temporal_data.to_csv(
    REPORT_DIR / "temporal_analysis.csv",
    index=False
)

# ==========================================
# 5. VISUALISATION GRAPHIQUE
# ==========================================

plt.figure(figsize=(12, 6))

for code, group in temporal_data.groupby("indicator_code"):

    plt.plot(
        group["year"],
        group["value"],
        marker="o",
        linewidth=2,
        label=code
    )

plt.title(
    "Evolution des indicateurs WASH au Congo",
    fontsize=14
)

plt.xlabel("Année")
plt.ylabel("Population (%)")

plt.legend(title="Indicateur")
plt.grid(True, alpha=0.3)
plt.tight_layout()

chart_file = REPORT_DIR / "wash_trends.png"

plt.savefig(chart_file, dpi=300)
plt.show()

# ==========================================
# 6. CONCLUSION AUTOMATIQUE
# ==========================================

print("\n--- SYNTHESE ---")

for _, row in statistics.iterrows():

    print(f"\nIndicateur : {row['indicator_code']}")
    print(f"Moyenne : {row['moyenne']} %")
    print(f"Minimum : {row['minimum']} %")
    print(f"Maximum : {row['maximum']} %")
    print(
        f"Période observée : "
        f"{int(row['premiere_annee'])} - "
        f"{int(row['derniere_annee'])}"
    )

print("\n==========================================")
print(" ANALYSE EXPLORATOIRE TERMINEE")
print("==========================================")

print("\nFichiers générés :")
print(REPORT_DIR / "descriptive_statistics.csv")
print(REPORT_DIR / "temporal_analysis.csv")
print(chart_file)
