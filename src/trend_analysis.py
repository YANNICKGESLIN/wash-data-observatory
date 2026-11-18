
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


REQUIRED_COLUMNS = {"indicator_code", "year", "value"}


def load_data(input_file: Path) -> pd.DataFrame:
    if not input_file.exists():
        raise FileNotFoundError(f"Fichier introuvable : {input_file}")

    df = pd.read_csv(input_file)
    missing_columns = REQUIRED_COLUMNS.difference(df.columns)

    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"Colonnes absentes : {missing_list}")

    df = df.copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    df = df.dropna(subset=["indicator_code", "year", "value"]).copy()
    df["indicator_code"] = df["indicator_code"].astype(str)

    return df.sort_values(["indicator_code", "year"]).reset_index(drop=True)


def compute_trend_results(df: pd.DataFrame):
    results = []
    annual_changes = []

    for code, group in df.groupby("indicator_code", sort=True):
        group = group.sort_values("year").copy()
        years = group["year"].to_numpy(dtype=float)
        values = group["value"].to_numpy(dtype=float)

        group["annual_change"] = group["value"].diff()

        if len(years) >= 2:
            slope, intercept = np.polyfit(years, values, 1)
            predicted = slope * years + intercept
            ss_res = np.sum((values - predicted) ** 2)
            ss_tot = np.sum((values - values.mean()) ** 2)
            r_squared = 1 - ss_res / ss_tot if ss_tot != 0 else np.nan
        else:
            slope, intercept = np.nan, np.nan
            r_squared = np.nan

        results.append(
            {
                "indicator_code": code,
                "first_year": int(years.min()),
                "last_year": int(years.max()),
                "initial_value": values[0],
                "final_value": values[-1],
                "total_change_pp": values[-1] - values[0],
                "average_linear_change_pp_per_year": slope,
                "r_squared": r_squared,
            }
        )

        group["indicator_code"] = code
        annual_changes.append(group)

    trend_results = pd.DataFrame(results)
    changes_df = pd.concat(annual_changes, ignore_index=True) if annual_changes else pd.DataFrame(columns=["indicator_code", "year", "value", "annual_change"])

    return trend_results, changes_df


def export_reports(report_dir: Path, trend_results: pd.DataFrame, changes_df: pd.DataFrame):
    report_dir.mkdir(parents=True, exist_ok=True)
    trend_results.to_csv(report_dir / "trend_analysis.csv", index=False)
    changes_df.to_csv(report_dir / "annual_changes.csv", index=False)


def plot_trends(report_dir: Path, changes_df: pd.DataFrame):
    for code, group in changes_df.groupby("indicator_code"):
        plt.figure(figsize=(10, 5))
        plt.plot(group["year"], group["value"], marker="o", label="Valeurs disponibles")
        plt.title(f"Tendance temporelle : {code}")
        plt.xlabel("Année")
        plt.ylabel("Population (%)")
        plt.grid(alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(report_dir / f"trend_{code}.png", dpi=300)
        plt.close()


def main():
    ROOT_DIR = Path(__file__).resolve().parent.parent
    INPUT_FILE = ROOT_DIR / "data/processed/congo_wash_analysis_ready.csv"
    REPORT_DIR = ROOT_DIR / "reports"

    print("\n==========================================")
    print(" WASH DATA OBSERVATORY")
    print(" TEMPORAL TREND ANALYSIS")
    print("==========================================")

    df = load_data(INPUT_FILE)
    trend_results, changes_df = compute_trend_results(df)
    export_reports(REPORT_DIR, trend_results, changes_df)

    print("\n--- TENDANCES DES INDICATEURS ---\n")
    if not trend_results.empty:
        print(trend_results.round(4).to_string(index=False))
    else:
        print("Aucune donnée exploitable pour calculer des tendances.")

    print("\n--- VARIATIONS ANNUELLES ---\n")
    if not changes_df.empty:
        for code, group in changes_df.groupby("indicator_code"):
            print(f"\nIndicateur : {code}")
            print(group[["year", "value", "annual_change"]].round(3).to_string(index=False))
    else:
        print("Aucune donnée annuelle disponible.")

    if not changes_df.empty:
        plot_trends(REPORT_DIR, changes_df)

    print("\n==========================================")
    print(" ANALYSE DES TENDANCES TERMINEE")
    print("==========================================")


if __name__ == "__main__":
    main()
