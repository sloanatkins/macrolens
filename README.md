# MacroLens: S&P 500 Sector Intelligence Pipeline

A production-style batch data pipeline that ingests daily S&P 500 sector ETF prices and Federal Reserve macroeconomic indicators, models them in a local data warehouse using dbt, and surfaces sector performance patterns across macro regimes in an interactive Streamlit dashboard.

Built as Project 1 of a data engineering portfolio targeting summer 2026 internships.

---

## Architecture

    Alpha Vantage API --> Python Ingestion --> PostgreSQL (raw) --> dbt Models --> Streamlit Dashboard
    FRED API          -->                  -->                  -->
                                  ^
                        Airflow DAG (6am weekdays)
                        Validation Layer (logged to DB)

---

## Tech Stack

| Layer | Tools |
|---|---|
| Ingestion | Python, requests, pandas |
| Orchestration | Apache Airflow (Astronomer CLI) |
| Storage | PostgreSQL |
| Transformation | dbt (staging to intermediate to mart) |
| Data Quality | Custom validation layer with DB logging |
| Dashboard | Streamlit, Plotly |
| Containerization | Docker, docker-compose |
| CI/CD | GitHub Actions |

---

## Data Sources

- **Alpha Vantage** - Daily OHLCV prices for 11 S&P 500 sector ETFs: XLK, XLF, XLV, XLE, XLI, XLP, XLY, XLU, XLB, XLRE, XLC
- **FRED** - 5 macroeconomic indicators going back to 2010: Fed Funds Rate, CPI, Unemployment Rate, 10Y-2Y Yield Spread, GDP

---

## Pipeline Stages

1. **Ingest** - Python scripts pull from Alpha Vantage and FRED APIs on a schedule
2. **Validate** - Row count, null, and range checks run before loading, logged to validation_log
3. **Load** - Raw data lands in PostgreSQL with ON CONFLICT DO NOTHING deduplication
4. **Transform** - dbt models clean, join, and aggregate across three layers
5. **Schedule** - Airflow DAG runs every weekday at 6am with 2 retries and failure handling
6. **Visualize** - Streamlit dashboard with Plotly charts, sidebar filters, and date range picker

---

## dbt Model Layers

    models/
    staging/
        stg_sector_prices.sql         cleans raw ETF prices, calculates daily_return_pct
        stg_macro_indicators.sql      cleans FRED indicators, filters nulls
    intermediate/
        int_sector_macro_joined.sql   joins sector prices to nearest macro observation date
    mart/
        mart_sector_performance.sql   macro regime labels + 30-day rolling returns

---

## Macro Regime Classification

| Regime | Condition |
|---|---|
| Restrictive | Fed rate >= 4% and yield spread < 0 |
| Tightening | Fed rate >= 4% and yield spread >= 0 |
| Expansionary | Fed rate < 2% and yield spread >= 0 |
| Recovery | Fed rate < 2% and yield spread < 0 |
| Neutral | All other conditions |

---

## Key Insights

- During the tightening regime (December 2025 - March 2026, Fed rate >= 3.5%), Consumer Discretionary and Industrials outperformed while Technology and Healthcare saw negative 30-day rolling returns, consistent with rate-sensitive growth sectors underperforming in elevated rate environments
- The yield spread remained positive throughout the observed period (0.5-1.0%), signaling no inversion despite elevated Fed rates near 3.6-4.3%, consistent with a soft landing scenario
- Sector return dispersion was highest in January 2026, with a ~1.2% spread between the best and worst performing sectors, suggesting macro uncertainty was driving rotation
- Energy was the most volatile sector on a 30-day rolling basis across both regimes, consistent with its sensitivity to oil price swings and geopolitical factors
- The pipeline classifies each trading day into one of five macro regimes based on Fed Funds Rate and 10Y-2Y yield spread, enabling direct comparison of sector behavior across different monetary policy environments

---

## How to Run

Prerequisites: Docker Desktop, Python 3.11+, Alpha Vantage API key from alphavantage.co, FRED API key from fred.stlouisfed.org

Setup:

    git clone https://github.com/sloanatkins/macrolens.git
    cd macrolens
    cp .env.example .env

Run the dashboard via Docker:

    docker-compose up --build

Dashboard available at localhost:8501

Run the pipeline manually:

    python ingestion/fetch_fred.py
    python ingestion/fetch_alpha_vantage.py
    python validation/validate.py

Run dbt transforms:

    cd dbt/macrolens
    dbt run
    dbt test

Run tests:

    pytest tests/test_ingestion.py -v

---

## Project Structure

    macrolens/
    .github/workflows/       GitHub Actions CI
    dags/                    Airflow DAG
    dashboard/               Streamlit app + Dockerfile
    dbt/macrolens/           dbt project
        models/
            staging/
            intermediate/
            mart/
    ingestion/               Alpha Vantage + FRED scripts
    scripts/                 DB initialization
    tests/                   pytest unit tests
    validation/              Data quality checks
    .env.example
    docker-compose.yml

---

## CI/CD

GitHub Actions runs on every push to main. Installs dependencies, lints with flake8, runs pytest.

---

Built with Python, Airflow, dbt, PostgreSQL, Streamlit, Docker, GitHub Actions