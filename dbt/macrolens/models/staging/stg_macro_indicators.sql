{#
  stg_macro_indicators
  ====================
  Cleans raw macroeconomic indicator data from raw_macro_indicators.

  Source: raw_macro_indicators (loaded by ingestion/fetch_fred.py)

  Indicators included:
  - fed_funds_rate     : Federal Funds Rate (monthly)
  - cpi                : Consumer Price Index (monthly)
  - unemployment_rate  : Unemployment Rate (monthly)
  - yield_spread_10y2y : 10Y-2Y Treasury Yield Spread (daily)
  - gdp                : Gross Domestic Product (quarterly)

  Transformations:
  - Filters out rows where value or date is null
  - No value transformations — raw FRED values are used as-is

  Materialized as: view
#}

with source as (
    select * from {{ source('macrolens', 'raw_macro_indicators') }}
),

cleaned as (
    select
        series_id,
        indicator,
        date,
        value,
        ingested_at
    from source
    -- Filter out any rows with missing values or dates
    where value is not null
      and date is not null
)

select * from cleaned