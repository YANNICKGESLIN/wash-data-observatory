from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_FILE = ROOT_DIR / "data" / "processed" / "wash_observatory.db"
RAW_FILE = ROOT_DIR / "data" / "raw" / "congo_wash_all_years.csv"
LOAD_SCRIPT = ROOT_DIR / "src" / "load_database.py"

EXPECTED_OBSERVATIONS = 198
EXPECTED_INDICATORS = 3


def rebuild_database():

    if not RAW_FILE.exists():
        raise FileNotFoundError(f"CSV introuvable : {RAW_FILE}")

    backup_file = None

    if DB_FILE.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = DB_FILE.with_name(
            f"wash_observatory_backup_before_rebuild_{timestamp}.db"
        )
        shutil.copy2(DB_FILE, backup_file)
        print(f"Sauvegarde créée : {backup_file.name}")

    try:
        print("\n1. Reconstruction des tables principales...")

        subprocess.run(
            [sys.executable, str(LOAD_SCRIPT)],
            cwd=ROOT_DIR,
            check=True
        )

        print("\n2. Préparation du journal d'extraction...")

        with sqlite3.connect(DB_FILE) as connection:
            connection.execute("DROP TABLE IF EXISTS extraction_logs")

        sys.path.insert(0, str(ROOT_DIR / "src"))

        from migrate_extraction_logs import migrate

        migrate()

        print("\n3. Vérification de la base...")

        with sqlite3.connect(DB_FILE) as connection:

            observations = connection.execute(
                "SELECT COUNT(*) FROM observations"
            ).fetchone()[0]

            indicators = connection.execute(
                "SELECT COUNT(*) FROM indicators"
            ).fetchone()[0]

            missing_values = connection.execute(
                "SELECT COUNT(*) FROM observations WHERE value IS NULL"
            ).fetchone()[0]

            linked = connection.execute(
                """
                SELECT COUNT(*)
                FROM observations o
                JOIN extraction_logs e
                    ON o.extraction_id = e.extraction_id
                """
            ).fetchone()[0]

            missing_extraction = connection.execute(
                """
                SELECT COUNT(*)
                FROM observations
                WHERE extraction_id IS NULL
                """
            ).fetchone()[0]

        print(f"Observations : {observations}")
        print(f"Indicateurs : {indicators}")
        print(f"Valeurs manquantes : {missing_values}")
        print(f"Observations liées à une extraction : {linked}")

        if observations != EXPECTED_OBSERVATIONS:
            raise ValueError("Nombre d'observations inattendu.")

        if indicators != EXPECTED_INDICATORS:
            raise ValueError("Nombre d'indicateurs inattendu.")

        if linked != observations or missing_extraction != 0:
            raise ValueError("Problème de traçabilité des observations.")

        print("\nRECONSTRUCTION TERMINEE AVEC SUCCES.")

        if backup_file:
            print(f"Sauvegarde précédente conservée : {backup_file.name}")

    except Exception:
        if backup_file and backup_file.exists():
            shutil.copy2(backup_file, DB_FILE)
            print("\nAncienne base restaurée.")

        raise


if __name__ == "__main__":
    rebuild_database()
