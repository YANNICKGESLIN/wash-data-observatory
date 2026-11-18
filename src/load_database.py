
from pathlib import Path
import sqlite3
import pandas as pd

# ==========================================
# 1. CONFIGURATION
# ==========================================

ROOT_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = ROOT_DIR / "data/raw/congo_wash_all_years.csv"

DB_FILE = ROOT_DIR / "data/processed/wash_observatory.db"

DB_FILE.parent.mkdir(parents=True, exist_ok=True)

print("\n==========================================")
print(" WASH DATA OBSERVATORY")
print(" SQL DATABASE MANAGEMENT")
print("==========================================")

# ==========================================
# 2. CHARGEMENT DES DONNEES
# ==========================================

df = pd.read_csv(INPUT_FILE)

df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["value"] = pd.to_numeric(df["value"], errors="coerce")

print(f"\nDonnées chargées : {len(df)} lignes")

# Vérifier les doublons avant insertion
keys = ["country_iso3", "indicator_code", "year"]

if df.duplicated(subset=keys).any():
    raise ValueError(
        "Des doublons existent. Vérification nécessaire avant insertion."
    )

# ==========================================
# 3. PREPARATION DES METADONNEES
# ==========================================

metadata_columns = [
    "indicator_code",
    "sdg_indicator",
    "indicator_name",
    "unit",
    "source",
    "original_source",
    "source_url"
]

indicators = df[metadata_columns].drop_duplicates()

if indicators["indicator_code"].duplicated().any():
    raise ValueError(
        "Métadonnées contradictoires pour un indicateur."
    )

# ==========================================
# 4. CONNEXION A SQLITE
# ==========================================

connection = sqlite3.connect(DB_FILE)

try:

    # Table des observations
    df.to_sql(
        "observations",
        connection,
        if_exists="replace",
        index=False
    )

    # Table des indicateurs
    indicators.to_sql(
        "indicators",
        connection,
        if_exists="replace",
        index=False
    )

    # Index pour accélérer les recherches
    connection.execute("""
        CREATE UNIQUE INDEX idx_observations_unique
        ON observations(country_iso3, indicator_code, year)
    """)

    connection.execute("""
        CREATE INDEX idx_observations_indicator
        ON observations(indicator_code)
    """)

    connection.commit()

    # ======================================
    # 5. VERIFICATION SQL
    # ======================================

    total = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM observations",
        connection
    )

    available = pd.read_sql_query("""
        SELECT
            indicator_code,
            COUNT(*) AS total_records,
            COUNT(value) AS available_values,
            COUNT(*) - COUNT(value) AS missing_values
        FROM observations
        GROUP BY indicator_code
    """, connection)

    print("\n--- VERIFICATION DE LA BASE ---")

    print("Total des observations :")
    print(total.to_string(index=False))

    print("\nRépartition par indicateur :")
    print(available.to_string(index=False))

    print("\nTables disponibles :")

    tables = pd.read_sql_query("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
    """, connection)

    print(tables.to_string(index=False))

finally:
    connection.close()

print("\nBase de données créée avec succès !")
print(f"Emplacement : {DB_FILE}")

print("\n==========================================")
print(" SQL DATABASE READY")
print("==========================================")
