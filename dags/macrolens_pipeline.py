"""
MacroLens Airflow DAG
=====================

Orchestrates the full MacroLens batch pipeline on a weekday schedule.
Runs every weekday at 6am, ingests data from two sources in parallel,
then validates before completing.

Pipeline structure:
    start
      ├── ingest_fred          (FRED macro indicators)
      └── ingest_sector_prices (Alpha Vantage ETF prices)
                ↓
          validate_data
                ↓
             end

Retry behavior:
- 2 retries per task with a 5-minute delay between attempts
- Alpha Vantage rate limit errors are caught and logged gracefully
  rather than triggering a retry

Schedule: 0 6 * * 1-5 (6am Monday through Friday)

Dependencies:
- Apache Airflow, ingestion.fetch_fred, ingestion.fetch_alpha_vantage,
  validation.validate
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
import sys
import os

# Add project root to path so ingestion and validation modules are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ingestion.fetch_fred import fetch_all_indicators, load_to_postgres as load_fred
from ingestion.fetch_alpha_vantage import fetch_daily_prices, load_to_postgres as load_av
from validation.validate import run_all_validations

# Default args applied to every task in the DAG
default_args = {
    "owner": "sloanatkins",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}


def ingest_fred():
    """
    Fetch all FRED macro indicators and load into raw_macro_indicators.

    Raises ValueError if FRED_API_KEY is not set in the environment.
    """
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise ValueError("FRED_API_KEY not set")
    df = fetch_all_indicators(api_key)
    load_fred(df)
    print(f"FRED ingestion complete: {len(df)} rows")


def ingest_sector_prices():
    """
    Fetch daily ETF prices for all 11 sector symbols and load into raw_sector_prices.

    Sleeps 12 seconds between each symbol to respect the Alpha Vantage
    free tier rate limit of 25 requests/day. If a rate limit error is
    detected mid-run, remaining symbols are skipped gracefully rather
    than failing the task.
    """
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
            time.sleep(12)  # stay within 25 req/day free tier limit
        except ValueError as e:
            if "Thank you for using Alpha Vantage" in str(e):
                # Rate limit hit — stop fetching, don't fail the task
                print(f"Rate limited on {symbol}, skipping remaining symbols")
                skipped += 1
                break
            raise
    print(f"Alpha Vantage ingestion complete: {total} rows, {skipped} symbols skipped due to rate limit")


def validate_data():
    """
    Run all data quality checks against raw tables.

    Raises ValueError if any check returns FAIL status, which causes
    Airflow to mark the task as failed and trigger retries.
    """
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

    # Dummy start operator — marks the beginning of the pipeline run
    start = EmptyOperator(task_id="start")

    # FRED and Alpha Vantage ingestion run in parallel
    ingest_fred_task = PythonOperator(
        task_id="ingest_fred",
        python_callable=ingest_fred,
    )

    ingest_prices_task = PythonOperator(
        task_id="ingest_sector_prices",
        python_callable=ingest_sector_prices,
    )

    # Validation runs only after both ingestion tasks complete
    validate_task = PythonOperator(
        task_id="validate_data",
        python_callable=validate_data,
    )

    # Dummy end operator — marks successful pipeline completion
    end = EmptyOperator(task_id="end")

    # DAG dependency graph: ingest in parallel, then validate, then done
    start >> [ingest_fred_task, ingest_prices_task] >> validate_task >> end