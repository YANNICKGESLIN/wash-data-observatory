
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

DB_FILE = ROOT_DIR / "data/processed/wash_observatory.db"

connection = sqlite3.connect(DB_FILE)

query = """
SELECT
    i.sdg_indicator,
    i.indicator_name,
    COUNT(o.value) AS available_values,
    ROUND(AVG(o.value), 2) AS average_value,
    ROUND(MIN(o.value), 2) AS minimum_value,
    ROUND(MAX(o.value), 2) AS maximum_value
FROM observations o
JOIN indicators i
    ON o.indicator_code = i.indicator_code
GROUP BY
    i.sdg_indicator,
    i.indicator_name
ORDER BY i.sdg_indicator;
"""

result = connection.execute(query).fetchall()

print("\n--- WASH SQL ANALYSIS ---\n")

for row in result:
    print(row)

connection.close()
