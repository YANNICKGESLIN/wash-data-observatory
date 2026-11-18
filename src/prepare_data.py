
from pathlib import Path
import pandas as pd

# ==========================================
# 1. CONFIGURATION
# ==========================================

ROOT_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = ROOT_DIR / "data/raw/congo_wash_all_years.csv"
OUTPUT_DIR = ROOT_DIR / "data/processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("\n==========================================")
print(" WASH DATA OBSERVATORY")
print(" DATA CLEANING & PREPARATION")
print("==========================================")

# ==========================================
# 2. CHARGEMENT
# ==========================================

df = pd.read_csv(INPUT_FILE)

initial_rows = len(df)

print(f"\nLignes initiales : {initial_rows}")

# ==========================================
# 3. NORMALISATION
# ==========================================

# Nettoyage des espaces dans les colonnes texte
text_columns = df.select_dtypes(
    include=["object", "str"]
).columns

for column in text_columns:
    df[column] = df[column].str.strip()

# Conversion des variables numériques
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["value"] = pd.to_numeric(df["value"], errors="coerce")

# ==========================================
# 4. DETECTION DES DOUBLONS
# ==========================================

duplicate_keys = [
    "country_iso3",
    "indicator_code",
    "year"
]

df["duplicate_key"] = df.duplicated(
    subset=duplicate_keys,
    keep=False
)

duplicate_count = int(df["duplicate_key"].sum())

# Nous conservons les doublons pour investigation.
# Aucune suppression automatique.

# ==========================================
# 5. VALIDATION
# ==========================================

df["missing_value"] = df["value"].isna()

df["valid_percentage"] = (
    df["value"].between(0, 100)
)

df["valid_year"] = (
    df["year"].notna()
    & df["year"].between(1900, 2026)
)

# ==========================================
# 6. CREATION DES JEUX DE DONNEES
# ==========================================

# Toutes les lignes sont conservées
clean_data = df.copy()

# Données utilisables pour l'analyse
analysis_ready = df[
    df["value"].notna()
    & df["valid_percentage"]
    & df["valid_year"]
    & ~df["duplicate_key"]
].copy()

# Conversion de l'année en entier
clean_data["year"] = clean_data["year"].astype("Int64")
analysis_ready["year"] = analysis_ready["year"].astype(int)

# ==========================================
# 7. EXPORTATION
# ==========================================

clean_file = OUTPUT_DIR / "congo_wash_clean.csv"

analysis_file = (
    OUTPUT_DIR / "congo_wash_analysis_ready.csv"
)

clean_data.to_csv(clean_file, index=False)

analysis_ready.to_csv(
    analysis_file,
    index=False
)

# ==========================================
# 8. RAPPORT FINAL
# ==========================================

print("\n--- RESULTATS DU NETTOYAGE ---")

print(f"Lignes initiales : {initial_rows}")
print(f"Lignes conservées : {len(clean_data)}")
print(f"Clés dupliquées : {duplicate_count}")
print(f"Valeurs manquantes : {df['missing_value'].sum()}")
print(f"Valeurs hors intervalle : {(~df['valid_percentage'] & df['value'].notna()).sum()}")
print(f"Années invalides : {(~df['valid_year']).sum()}")

print("\n--- DONNEES PRETES POUR ANALYSE ---")

print(f"Observations valides : {len(analysis_ready)}")

print("\n--- FICHIERS GENERES ---")

print(clean_file)
print(analysis_file)

print("\n==========================================")
print(" PREPARATION TERMINEE AVEC SUCCES")
print("==========================================")
