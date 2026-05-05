import os
import requests
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv
import time

load_dotenv()

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# Macro indicators we want from FRED
FRED_SERIES = {
    "FEDFUNDS": "fed_funds_rate",
    "CPIAUCSL": "cpi",
    "UNRATE":   "unemployment_rate",
    "T10Y2Y":   "yield_spread_10y2y",
    "GDP":      "gdp",
}


def fetch_fred_series(series_id: str, api_key: str) -> pd.DataFrame:
    """Fetch a single FRED series and return as a clean DataFrame."""
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": "2010-01-01",
    }

    response = requests.get(FRED_BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()

    if "observations" not in data:
        raise ValueError(f"Unexpected response for {series_id}: {data}")

    rows = []
    for obs in data["observations"]:
        if obs["value"] == ".":  # FRED uses "." for missing values
            continue
        rows.append({
            "series_id": series_id,
            "indicator": FRED_SERIES[series_id],
            "date": obs["date"],
            "value": float(obs["value"]),
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        })

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def fetch_all_indicators(api_key: str) -> pd.DataFrame:
    """Fetch all macro indicators and combine into one DataFrame."""
    all_dfs = []

    for series_id, indicator_name in FRED_SERIES.items():
        print(f"Fetching {series_id} ({indicator_name})...")
        try:
            df = fetch_fred_series(series_id, api_key)
            all_dfs.append(df)
            time.sleep(1)
        except Exception as e:
            print(f"ERROR fetching {series_id}: {e}")

    return pd.concat(all_dfs, ignore_index=True)

def load_to_postgres(df: pd.DataFrame) -> None:
    """Load macro indicators DataFrame into raw_macro_indicators table."""
    import psycopg2

    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432),
        dbname=os.getenv("POSTGRES_DB", "macrolens"),
        user=os.getenv("POSTGRES_USER", os.environ.get("USER")),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )

    with conn.cursor() as cur:
        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO raw_macro_indicators
                    (series_id, indicator, date, value, ingested_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (series_id, date) DO NOTHING;
            """, (
                row["series_id"],
                row["indicator"],
                row["date"].date(),
                row["value"],
                row["ingested_at"],
            ))

    conn.commit()
    conn.close()
    print(f"Loaded {len(df)} rows into raw_macro_indicators.")

if __name__ == "__main__":
    api_key = os.getenv("FRED_API_KEY")
    print(f"API key loaded: {bool(api_key)}")

    if not api_key:
        raise ValueError("FRED_API_KEY not set in .env")

    df = fetch_all_indicators(api_key)
    print(df.head(10))
    print(f"\nTotal rows: {len(df)}")
    print(f"\nIndicators fetched: {df['indicator'].unique()}")

    load_to_postgres(df)