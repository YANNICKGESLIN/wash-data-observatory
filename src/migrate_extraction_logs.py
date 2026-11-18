from pathlib import Path
import sqlite3
import uuid

DB_FILE = Path(__file__).resolve().parents[1] / "data" / "processed" / "wash_observatory.db"

def migrate():
    if not DB_FILE.exists():
        raise FileNotFoundError(f"Database not found: {DB_FILE}")

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(observations)")
        }

        if "extraction_id" in columns:
            assigned = conn.execute(
                "SELECT COUNT(*) FROM observations WHERE extraction_id IS NOT NULL"
            ).fetchone()[0]

            total = conn.execute(
                "SELECT COUNT(*) FROM observations"
            ).fetchone()[0]

            if assigned == total:
                print("Migration already completed. No changes made.")
                return

        conn.execute("""
            CREATE TABLE IF NOT EXISTS extraction_logs (
                extraction_id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                country_iso3 TEXT NOT NULL,
                source TEXT,
                original_source TEXT,
                observation_count INTEGER NOT NULL,
                indicator_count INTEGER NOT NULL,
                status TEXT NOT NULL,
                notes TEXT
            )
        """)

        if "extraction_id" not in columns:
            conn.execute("""
                ALTER TABLE observations
                ADD COLUMN extraction_id TEXT
                REFERENCES extraction_logs(extraction_id)
            """)

        stats = conn.execute("""
            SELECT
                COUNT(*),
                MIN(retrieved_at),
                MAX(retrieved_at),
                MAX(country_iso3),
                GROUP_CONCAT(DISTINCT source),
                GROUP_CONCAT(DISTINCT original_source),
                COUNT(DISTINCT indicator_code)
            FROM observations
            WHERE extraction_id IS NULL
        """).fetchone()

        count, started, completed, country, source, original_source, indicators = stats

        if count == 0:
            print("No unlinked observations found.")
            return

        extraction_id = str(uuid.uuid4())

        conn.execute("""
            INSERT INTO extraction_logs (
                extraction_id,
                started_at,
                completed_at,
                country_iso3,
                source,
                original_source,
                observation_count,
                indicator_count,
                status,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            extraction_id,
            started,
            completed,
            country,
            source,
            original_source,
            count,
            indicators,
            "historical_import",
            "Historical extraction reconstructed from existing retrieved_at timestamps. "
            "This record documents one extraction process, not separate extractions."
        ))

        conn.execute("""
            UPDATE observations
            SET extraction_id = ?
            WHERE extraction_id IS NULL
        """, (extraction_id,))

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_observations_extraction
            ON observations(extraction_id)
        """)

        print("Migration completed successfully.")
        print(f"Extraction ID: {extraction_id}")
        print(f"Linked observations: {count}")
        print(f"Indicators: {indicators}")
        print(f"Country: {country}")
        print(f"Extraction start: {started}")
        print(f"Extraction end: {completed}")

if __name__ == "__main__":
    migrate()
