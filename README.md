# MacroLens: S&P 500 Sector Intelligence Pipeline

A production-style batch data pipeline that ingests daily S&P 500 sector ETF prices and Federal Reserve macroeconomic indicators, models them in a local data warehouse using dbt, and surfaces sector performance patterns across macro regimes in an interactive Streamlit dashboard.

Built as Project 1 of a data engineering portfolio targeting summer 2026 internships.

![MacroLens Dashboard](assets/dashboard.png)
![MacroLens Dashboard](assets/dashboard2.png)

---

## What This Does

MacroLens answers a specific question: which S&P 500 sectors outperform or underperform depending on what the Fed is doing? It pulls daily ETF price data and monthly macro indicators, joins them, classifies each trading day into a macro regime, and lets you explore sector performance visually across those regimes.

The pipeline runs automatically every weekday at 6am via Airflow. Data flows from two public APIs through validation, into PostgreSQL, through dbt transformations, and into a Streamlit dashboard.

---

## Architecture

    Alpha Vantage API --> Python Ingestion --> PostgreSQL (raw tables)
    FRED API          -->                  -->
                                                --> dbt (staging > intermediate > mart)
                                                        --> Streamlit + Plotly Dashboard
                          Airflow DAG orchestrates the full pipeline
                          Validation layer logs results to validation_log table

---

## Tech Stack

| Layer | Tools |
|---|---|
| Ingestion | Python, requests, pandas |
| Orchestration | Apache Airflow via Astronomer CLI |
| Storage | PostgreSQL |
| Transformation | dbt with staging, intermediate, and mart layers |
| Data Quality | Custom validation layer with pass/fail logging to DB |
| Dashboard | Streamlit, Plotly |
| Containerization | Docker, docker-compose |
| CI/CD | GitHub Actions |

---

## Data Sources

Alpha Vantage: Daily OHLCV prices for 11 S&P 500 sector ETFs going back 100 trading days per run. Symbols: XLK, XLF, XLV, XLE, XLI, XLP, XLY, XLU, XLB, XLRE, XLC. Free API key required, 25 requests per day on the free tier.

FRED (Federal Reserve Economic Data): 5 macroeconomic indicators from 2010 to present. Fed Funds Rate, CPI, Unemployment Rate, 10Y-2Y Yield Spread, GDP. Free API key required, no meaningful rate limit.

---

## Pipeline Stages

1. Ingest: Python scripts call Alpha Vantage and FRED APIs, parse JSON responses, and return clean pandas DataFrames
2. Validate: Row count, null checks, and range checks run before loading. Every result is logged to the validation_log table with PASS, FAIL, or WARN status
3. Load: Data inserts into PostgreSQL raw tables using ON CONFLICT DO NOTHING to handle duplicate runs safely
4. Transform: dbt runs three model layers to clean, join, and aggregate the data
5. Schedule: Airflow DAG runs every weekday at 6am with 2 automatic retries and 5 minute retry delay
6. Visualize: Streamlit dashboard with Plotly charts, sidebar filters for sector, regime, and date range

---

## dbt Model Layers

staging layer cleans raw data and adds calculated fields. stg_sector_prices adds daily_return_pct calculated as (close - open) / open * 100. stg_macro_indicators filters nulls and standardizes column names.

intermediate layer joins the two datasets. int_sector_macro_joined uses a nearest-date join to attach the most recent available macro observation to each trading day, with forward-fill to handle gaps between monthly FRED releases.

mart layer produces the final analytics table. mart_sector_performance adds macro regime classification and a 30-day rolling average return per sector using window functions.

---

## Macro Regime Classification

Each trading day is classified based on the Fed Funds Rate and 10Y-2Y yield spread:

| Regime | Condition |
|---|---|
| Restrictive | Fed rate >= 5% and yield spread < 0 |
| Tightening | Fed rate >= 3.5% and yield spread >= 0 |
| Expansionary | Fed rate < 2% and yield spread >= 0 |
| Recovery | Fed rate < 2% and yield spread < 0 |
| Neutral | All other conditions |

---

## Key Insights

- During the tightening regime (December 2025 through March 2026, Fed rate >= 3.5%), Consumer Discretionary and Industrials outperformed while Technology and Healthcare saw negative 30-day rolling returns, consistent with rate-sensitive growth sectors underperforming in elevated rate environments
- The yield spread remained positive throughout the observed period (0.5 to 1.0%), signaling no inversion despite elevated Fed rates near 3.6 to 4.3%, consistent with a soft landing scenario
- Sector return dispersion was highest in January 2026, with a 1.2% spread between the best and worst performing sectors, suggesting macro uncertainty was driving rotation between sectors
- Energy was the most volatile sector on a 30-day rolling basis across both regimes, consistent with its sensitivity to oil price swings and geopolitical factors
- The pipeline classifies each trading day into one of five macro regimes based on Fed Funds Rate and 10Y-2Y yield spread, enabling direct comparison of sector behavior across different monetary policy environments

---

## How to Run

### Prerequisites

Docker Desktop installed and running. That is all you need to run the dashboard. To run the full pipeline yourself you also need a free Alpha Vantage API key from alphavantage.co and a free FRED API key from fred.stlouisfed.org.

### Run the dashboard with Docker (recommended)

This spins up the dashboard and a pre-seeded Postgres database with no additional setup required.

    git clone https://github.com/sloanatkins/macrolens.git
    cd macrolens
    docker-compose up --build

Dashboard available at localhost:8501. The database is automatically seeded with real data on first startup.

### Run the full pipeline yourself

If you want to ingest fresh data from the APIs:

    git clone https://github.com/sloanatkins/macrolens.git
    cd macrolens
    cp .env.example .env

Add your API keys to .env, then:

    pip install -r requirements.txt
    python scripts/init_db.py
    python ingestion/fetch_fred.py
    python ingestion/fetch_alpha_vantage.py
    python validation/validate.py

Run dbt transforms:

    cd dbt/macrolens
    dbt run
    dbt test

Start the dashboard:

    cd ../..
    streamlit run dashboard/app.py

### Run the Airflow pipeline

    astro dev start

Airflow UI available at localhost:8080. The macrolens_pipeline DAG runs every weekday at 6am or can be triggered manually.

### Run tests

    pytest tests/test_ingestion.py -v

---

## Project Structure

    macrolens/
    .github/workflows/       GitHub Actions CI pipeline
    dags/                    Airflow DAG definition
    dashboard/               Streamlit app and Dockerfile
    dbt/macrolens/           dbt project
        models/
            staging/         stg_sector_prices, stg_macro_indicators
            intermediate/    int_sector_macro_joined
            mart/            mart_sector_performance
    ingestion/               fetch_alpha_vantage.py, fetch_fred.py
    scripts/                 init_db.py, schema.sql, seed.sql
    tests/                   pytest unit tests
    validation/              validate.py with logging to validation_log
    .env.example             template for environment variables
    docker-compose.yml       runs dashboard and seeded Postgres

---

## Environment Variables

Copy .env.example to .env and fill in your values:

    ALPHA_VANTAGE_API_KEY=your_key_here
    FRED_API_KEY=your_key_here
    POSTGRES_HOST=localhost
    POSTGRES_PORT=5432
    POSTGRES_DB=macrolens
    POSTGRES_USER=your_username
    POSTGRES_PASSWORD=

---

## CI/CD

GitHub Actions runs on every push to main. It installs dependencies, lints with flake8, and runs the pytest suite. See .github/workflows/ci.yml for the full workflow.

---

Built with Python, Apache Airflow, dbt, PostgreSQL, Streamlit, Plotly, Docker, and GitHub Actions