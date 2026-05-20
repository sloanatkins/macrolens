from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ingestion.fetch_fred import fetch_all_indicators, load_to_postgres as load_fred
from ingestion.fetch_alpha_vantage import fetch_daily_prices, load_to_postgres as load_av
from validation.validate import run_all_validations

default_args = {
    "owner": "sloanatkins",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

def ingest_fred():
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise ValueError("FRED_API_KEY not set")
    df = fetch_all_indicators(api_key)
    load_fred(df)
    print(f"FRED ingestion complete: {len(df)} rows")

def ingest_sector_prices():
    symbols = [
        "XLK", "XLF", "XLV", "XLE", "XLI",
        "XLP", "XLY", "XLU", "XLB", "XLRE", "XLC"
    ]
    import time
    total = 0
    skipped = 0
    for symbol in symbols:
        try:
            df = fetch_daily_prices(symbol)
            load_av(df)
            total += len(df)
            time.sleep(12)
        except ValueError as e:
            if "Thank you for using Alpha Vantage" in str(e):
                print(f"Rate limited on {symbol}, skipping remaining symbols")
                skipped += 1
                break
            raise
    print(f"Alpha Vantage ingestion complete: {total} rows, {skipped} symbols skipped due to rate limit")

    
def validate_data():
    passed = run_all_validations()
    if not passed:
        raise ValueError("Validation failed — check validation_log table")

with DAG(
    dag_id="macrolens_pipeline",
    default_args=default_args,
    description="MacroLens: ingest sector ETF prices and macro indicators daily",
    schedule="0 6 * * 1-5",  # 6am every weekday
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["macrolens", "finance", "batch"],
) as dag:

    start = EmptyOperator(task_id="start")

    ingest_fred_task = PythonOperator(
        task_id="ingest_fred",
        python_callable=ingest_fred,
    )

    ingest_prices_task = PythonOperator(
        task_id="ingest_sector_prices",
        python_callable=ingest_sector_prices,
    )

    validate_task = PythonOperator(
        task_id="validate_data",
        python_callable=validate_data,
    )

    end = EmptyOperator(task_id="end")

    start >> [ingest_fred_task, ingest_prices_task] >> validate_task >> end