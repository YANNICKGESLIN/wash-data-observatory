from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests


# Configuration du projet
BASE_URL = "https://api.worldbank.org/v2"
COUNTRY = "COG"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

INDICATORS = {
    "SH.H2O.SMDW.ZS": {
        "sdg": "6.1.1",
        "name": "Safely managed drinking water"
    },
    "SH.STA.SMSS.ZS": {
        "sdg": "6.2.1a",
        "name": "Safely managed sanitation"
    },
    "SH.STA.HYGN.ZS": {
        "sdg": "6.2.1b",
        "name": "Basic handwashing facilities"
    }
}


def fetch_indicator(session, code, metadata):
    """Télécharge toutes les observations disponibles d'un indicateur."""

    url = f"{BASE_URL}/country/{COUNTRY}/indicator/{code}"
    observations = []
    page = 1

    while True:
        params = {
            "format": "json",
            "per_page": 20000,
            "page": page
        }

        response = session.get(
            url,
            params=params,
            timeout=30
        )
        response.raise_for_status()

        payload = response.json()

        if not isinstance(payload, list) or len(payload) < 2:
            raise ValueError(f"Réponse API inattendue pour {code}")

        pagination = payload[0]
        records = payload[1] or []

        for item in records:
            country = item.get("country") or {}
            indicator = item.get("indicator") or {}

            observations.append({
                "country": country.get("value"),
                "country_iso3": COUNTRY,
                "sdg_indicator": metadata["sdg"],
                "indicator_code": code,
                "indicator_name": indicator.get("value"),
                "year": item.get("date"),
                "value": item.get("value"),
                "unit": item.get("unit") or "% of population",
                "source": "World Bank - World Development Indicators",
                "original_source": "WHO/UNICEF Joint Monitoring Programme",
                "source_url": url,
                "retrieved_at": datetime.now(
                    timezone.utc
                ).isoformat()
            })

        total_pages = pagination.get("pages", 1)

        if page >= total_pages:
            break

        page += 1

    return observations


def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "WASH-Data-Observatory/1.0"
    })

    all_observations = []

    for code, metadata in INDICATORS.items():
        print(f"\nCollecte : {metadata['name']} ({code})")

        try:
            records = fetch_indicator(
                session,
                code,
                metadata
            )

            all_observations.extend(records)

            available = sum(
                row["value"] is not None for row in records
            )

            print(f"Observations reçues : {len(records)}")
            print(f"Valeurs non manquantes : {available}")

        except requests.RequestException as error:
            print(f"Erreur réseau pour {code} : {error}")

        except (ValueError, KeyError) as error:
            print(f"Erreur de données pour {code} : {error}")

    if not all_observations:
        raise RuntimeError(
            "Aucune observation récupérée. Vérifie la connexion "
            "et la disponibilité de l'API."
        )

    df = pd.DataFrame(all_observations)

    # Conversion des années et valeurs numériques
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Conservation de toutes les observations reçues
    raw_file = RAW_DIR / "congo_wash_all_years.csv"
    df.to_csv(raw_file, index=False, encoding="utf-8-sig")

    # Dernière observation non manquante pour chaque indicateur
    valid = df.dropna(subset=["year", "value"]).copy()

    if valid.empty:
        raise RuntimeError(
            "Aucune valeur exploitable pour produire le fichier final."
        )

    latest = (
        valid.sort_values("year")
        .groupby("indicator_code", as_index=False)
        .tail(1)
        .sort_values("sdg_indicator")
    )

    latest_file = PROCESSED_DIR / "congo_wash_latest.csv"
    latest.to_csv(latest_file, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 55)
    print("COLLECTE TERMINÉE")
    print("=" * 55)
    print("\nDernières observations disponibles :")
    print(
        latest[
            ["sdg_indicator", "indicator_name", "year", "value"]
        ].to_string(index=False)
    )

    print(f"\nDonnées brutes : {raw_file}")
    print(f"Données traitées : {latest_file}")


if __name__ == "__main__":
    main()
