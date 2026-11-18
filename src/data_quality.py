
from pathlib import Path
from datetime import datetime

import pandas as pd

# ==========================================
# 1. CONFIGURATION
# ==========================================

ROOT_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = ROOT_DIR / "data" / "raw" / "congo_wash_all_years.csv"
REPORT_DIR = ROOT_DIR / "reports"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"

REPORT_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# 2. CHARGEMENT DES DONNEES
# ==========================================

print("\n" + "=" * 55)
print("       WASH DATA OBSERVATORY")
print("       DATA QUALITY ASSESSMENT")
print("=" * 55)

if not INPUT_FILE.exists():
    raise FileNotFoundError(f"Fichier introuvable : {INPUT_FILE}")

df = pd.read_csv(INPUT_FILE)

print(f"\nNombre total de lignes : {len(df)}")
print(f"Nombre de colonnes : {len(df.columns)}")

# ==========================================
# 3. CONTROLE DE COMPLETUDE
# ==========================================

required_columns = [
    "country_iso3",
    "indicator_code",
    "year",
    "value"
]

missing_columns = [
    col for col in required_columns if col not in df.columns
]

if missing_columns:
    raise ValueError(f"Colonnes absentes : {missing_columns}")

df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["value"] = pd.to_numeric(df["value"], errors="coerce")

completeness = (
    df.groupby(["indicator_code", "sdg_indicator"])
    .agg(
        total_records=("year", "size"),
        available_values=("value", "count"),
        missing_values=("value", lambda x: x.isna().sum()),
        first_year=("year", "min"),
        last_year=("year", "max")
    )
    .reset_index()
)

completeness["completeness_rate"] = (
    completeness["available_values"]
    / completeness["total_records"] * 100
).round(2)

# ==========================================
# 4. DETECTION DES DOUBLONS
# ==========================================

duplicate_columns = [
    "country_iso3",
    "indicator_code",
    "year"
]

duplicates = df.duplicated(
    subset=duplicate_columns,
    keep=False
)

duplicate_count = int(duplicates.sum())

# ==========================================
# 5. VALIDATION DES VALEURS
# ==========================================

# Nos trois indicateurs sont exprimés en pourcentage.
# Les valeurs doivent donc être comprises entre 0 et 100.

out_of_range = df[
    df["value"].notna()
    & ~df["value"].between(0, 100)
]

invalid_years = df[
    df["year"].isna()
    | (df["year"] < 1900)
    | (df["year"] > datetime.now().year)
]

# ==========================================
# 6. STATUT DES INDICATEURS
# ==========================================

def determine_status(rate):
    if rate == 0:
        return "NO DATA"
    elif rate < 50:
        return "LOW COMPLETENESS"
    elif rate < 100:
        return "PARTIAL DATA"
    return "COMPLETE"

completeness["status"] = (
    completeness["completeness_rate"]
    .apply(determine_status)
)

# ==========================================
# 7. GENERATION DES RAPPORTS
# ==========================================

report_file = REPORT_DIR / "data_quality_report.csv"

completeness.to_csv(
    report_file,
    index=False
)

# Export des lignes contenant des valeurs manquantes
missing_data = df[df["value"].isna()]

missing_data.to_csv(
    PROCESSED_DIR / "missing_data.csv",
    index=False
)

# ==========================================
# 8. RAPPORT CONSOLE
# ==========================================

print("\n--- COMPLETUDE DES INDICATEURS ---\n")

print(completeness.to_string(index=False))

print("\n--- CONTROLE GENERAL ---")

print(f"Total des doublons détectés : {duplicate_count}")
print(f"Valeurs hors intervalle 0-100 : {len(out_of_range)}")
print(f"Années invalides : {len(invalid_years)}")
print(f"Données manquantes : {df['value'].isna().sum()}")

print("\n--- FICHIERS GENERES ---")

print(f"Rapport qualité : {report_file}")
print(f"Données manquantes : {PROCESSED_DIR / 'missing_data.csv'}")

print("\n" + "=" * 55)
print("ANALYSE TERMINEE AVEC SUCCES")
print("=" * 55)
