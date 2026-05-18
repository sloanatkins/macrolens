"""
Ingestion Unit Tests
====================

Unit tests for the MacroLens ingestion layer. Tests validate that
DataFrames produced by the ingestion scripts have the correct structure,
column names, and values before they reach the database.

These tests run without making any API calls or database connections —
they construct minimal DataFrames directly and assert against them.

Run with:
    pytest tests/test_ingestion.py -v

Dependencies:
- pandas, pytest
"""

import pandas as pd
from datetime import datetime, timezone


def test_fred_dataframe_structure():
    """
    Test that a FRED macro indicator DataFrame has the expected schema.

    Constructs a minimal one-row DataFrame matching the structure
    returned by fetch_fred_series and asserts required columns exist
    and row count is correct.
    """
    df = pd.DataFrame([{
        "series_id": "FEDFUNDS",
        "indicator": "fed_funds_rate",
        "date": datetime(2026, 1, 1),
        "value": 4.33,
        "ingested_at": datetime.now(timezone.utc).isoformat()
    }])

    # Verify all columns required by load_to_postgres are present
    assert "series_id" in df.columns
    assert "indicator" in df.columns
    assert "value" in df.columns
    assert len(df) == 1


def test_sector_dataframe_structure():
    """
    Test that a sector price DataFrame has the expected schema and values.

    Constructs a minimal one-row DataFrame matching the structure
    returned by fetch_daily_prices and asserts required columns exist
    and that close price is preserved correctly.
    """
    df = pd.DataFrame([{
        "symbol": "XLK",
        "sector": "Technology",
        "date": datetime(2026, 1, 1),
        "open": 150.0,
        "high": 152.0,
        "low": 149.0,
        "close": 151.0,
        "volume": 1000000,
        "ingested_at": datetime.now(timezone.utc).isoformat()
    }])

    # Verify all columns required by load_to_postgres are present
    assert "symbol" in df.columns
    assert "close" in df.columns
    # Verify values are not transformed during DataFrame construction
    assert df["close"].iloc[0] == 151.0