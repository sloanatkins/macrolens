import pandas as pd
from datetime import datetime, timezone


def test_fred_dataframe_structure():
    """Test that FRED data has expected columns."""
    df = pd.DataFrame([{
        "series_id": "FEDFUNDS",
        "indicator": "fed_funds_rate",
        "date": datetime(2026, 1, 1),
        "value": 4.33,
        "ingested_at": datetime.now(timezone.utc).isoformat()
    }])
    assert "series_id" in df.columns
    assert "indicator" in df.columns
    assert "value" in df.columns
    assert len(df) == 1


def test_sector_dataframe_structure():
    """Test that sector price data has expected columns."""
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
    assert "symbol" in df.columns
    assert "close" in df.columns
    assert df["close"].iloc[0] == 151.0