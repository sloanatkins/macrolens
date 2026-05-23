{#
  stg_sector_prices
  =================
  Cleans raw ETF price data from raw_sector_prices and calculates
  daily return percentage.

  Source: raw_sector_prices (loaded by ingestion/fetch_alpha_vantage.py)

  Transformations:
  - Filters out rows where close or date is null
  - Adds daily_return_pct: (close - open) / open * 100, rounded to 4dp

  Materialized as: view
#}

with source as (
    select * from {{ source('macrolens', 'raw_sector_prices') }}
),

cleaned as (
    select
        symbol,
        sector,
        date,
        open,
        high,
        low,
        close,
        volume,
        -- Daily return as a percentage of the opening price
        round((close - open) / open * 100, 4) as daily_return_pct,
        ingested_at
    from source
    where close is not null
      and date is not null
)

select * from cleaned