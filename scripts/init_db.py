"""
Database Initialization
=======================

Creates the raw PostgreSQL tables used by the MacroLens pipeline.
Run this once before the first pipeline execution to set up the schema.

Tables created:
- raw_sector_prices    : daily OHLCV prices per sector ETF from Alpha Vantage
- raw_macro_indicators : macroeconomic indicator observations from FRED
- validation_log       : audit trail of all data quality check results

All tables use IF NOT EXISTS so this script is safe to re-run without
dropping existing data.

Dependencies:
- psycopg2, python-dotenv
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Return a psycopg2 connection using environment variables."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432),
        dbname=os.getenv("POSTGRES_DB", "macrolens"),
        user=os.getenv("POSTGRES_USER", os.environ.get("USER")),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )


def create_tables(conn):
    """
    Create all pipeline tables if they do not already exist.

    raw_sector_prices:
        Stores daily OHLCV price data per ETF symbol. Unique constraint
        on (symbol, date) prevents duplicate ingestion runs from
        inserting duplicate rows.

    raw_macro_indicators:
        Stores FRED time series observations. Unique constraint on
        (series_id, date) prevents duplicates across runs.

    validation_log:
        Append-only audit log. Every validation check writes one row
        with its table name, check name, status, and message.

    Parameters
    ----------
    conn : psycopg2 connection
    """
    with conn.cursor() as cur:

        # Daily ETF price data — one row per symbol per trading day
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw_sector_prices (
                id              SERIAL PRIMARY KEY,
                symbol          VARCHAR(10) NOT NULL,
                sector          VARCHAR(50) NOT NULL,
                date            DATE NOT NULL,
                open            NUMERIC(10, 4),
                high            NUMERIC(10, 4),
                low             NUMERIC(10, 4),
                close           NUMERIC(10, 4),
                volume          BIGINT,
                ingested_at     TIMESTAMPTZ NOT NULL,
                UNIQUE(symbol, date)
            );
        """)

        # FRED macroeconomic observations — one row per series per date
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw_macro_indicators (
                id              SERIAL PRIMARY KEY,
                series_id       VARCHAR(20) NOT NULL,
                indicator       VARCHAR(50) NOT NULL,
                date            DATE NOT NULL,
                value           NUMERIC(12, 4),
                ingested_at     TIMESTAMPTZ NOT NULL,
                UNIQUE(series_id, date)
            );
        """)

        # Validation audit log — append-only, never updated
        cur.execute("""
            CREATE TABLE IF NOT EXISTS validation_log (
                id              SERIAL PRIMARY KEY,
                table_name      VARCHAR(50) NOT NULL,
                check_name      VARCHAR(100) NOT NULL,
                status          VARCHAR(10) NOT NULL,
                message         TEXT,
                checked_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)

    conn.commit()
    print("Tables created successfully.")


if __name__ == "__main__":
    conn = get_connection()
    create_tables(conn)
    conn.close()