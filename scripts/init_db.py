import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432),
        dbname=os.getenv("POSTGRES_DB", "macrolens"),
        user=os.getenv("POSTGRES_USER", os.environ.get("USER")),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )


def create_tables(conn):
    with conn.cursor() as cur:
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