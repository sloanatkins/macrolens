import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import time
from datetime import timezone

load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

# S&P 500 sector ETFs
SECTOR_ETFS = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLV": "Healthcare",
    "XLE": "Energy",
    "XLI": "Industrials",
    "XLP": "Consumer Staples",
    "XLY": "Consumer Discretionary",
    "XLU": "Utilities",
    "XLB": "Materials",
    "XLRE": "Real Estate",
    "XLC": "Communication Services",
}


def fetch_daily_prices(symbol: str) -> pd.DataFrame:
    """Fetch daily adjusted prices for a single ETF symbol."""
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "compact",  # last 100 trading days
        "apikey": API_KEY,
    }

    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()

    if "Time Series (Daily)" not in data:
        raise ValueError(f"Unexpected response for {symbol}: {data}")

    time_series = data["Time Series (Daily)"]

    rows = []
    for date_str, values in time_series.items():
        rows.append({
            "symbol": symbol,
            "sector": SECTOR_ETFS[symbol],
            "date": date_str,
            "open": float(values["1. open"]),
            "high": float(values["2. high"]),
            "low": float(values["3. low"]),
            "close": float(values["4. close"]),
            "volume": int(values["5. volume"]),
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        })

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    return df


def fetch_all_sectors() -> pd.DataFrame:
    """Fetch daily prices for all sector ETFs and combine into one DataFrame."""
    all_dfs = []

    for symbol in SECTOR_ETFS:
        print(f"Fetching {symbol}...")
        try:
            df = fetch_daily_prices(symbol)
            all_dfs.append(df)
            time.sleep(12)  # stay well under 25 req/day limit
        except Exception as e:
            print(f"ERROR fetching {symbol}: {e}")

    return pd.concat(all_dfs, ignore_index=True)


def load_to_postgres(df: pd.DataFrame) -> None:
    """Load sector prices DataFrame into raw_sector_prices table."""
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
                INSERT INTO raw_sector_prices
                    (symbol, sector, date, open, high, low, close, volume, ingested_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, date) DO NOTHING;
            """, (
                row["symbol"],
                row["sector"],
                row["date"].date(),
                row["open"],
                row["high"],
                row["low"],
                row["close"],
                row["volume"],
                row["ingested_at"],
            ))

    conn.commit()
    conn.close()
    print(f"Loaded {len(df)} rows into raw_sector_prices.")


if __name__ == "__main__":
    df = fetch_all_sectors()
    print(df.head())
    print(f"\nTotal rows: {len(df)}")
    load_to_postgres(df)