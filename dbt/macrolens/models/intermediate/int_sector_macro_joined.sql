{#
  int_sector_macro_joined
  =======================
  Joins daily sector ETF prices to macroeconomic indicators by nearest
  available observation date.

  Sources:
  - stg_sector_prices     : daily OHLCV data per ETF symbol
  - stg_macro_indicators  : FRED macro indicators (mixed frequencies)

  The challenge: macro indicators are released at different frequencies
  (monthly for Fed Funds Rate/CPI/unemployment, daily for yield spread,
  quarterly for GDP). This model handles the frequency mismatch in two steps:

  Step 1 — macro_wide:
    Pivots the long-format indicator table into wide format so each
    date has one row with all indicators as columns.

  Step 2 — macro_filled:
    Forward-fills null values using lag() + coalesce() so that monthly
    and quarterly indicators propagate across daily trading dates.
    Without this, most trading days would have null macro values.

  Step 3 — joined:
    Left joins sector prices to the forward-filled macro table using a
    nearest-date subquery — for each trading day, finds the most recent
    macro observation on or before that date.

  Materialized as: view
#}

with sector_prices as (
    select * from {{ ref('stg_sector_prices') }}
),

macro_indicators as (
    select * from {{ ref('stg_macro_indicators') }}
),

-- Pivot long-format indicators into wide format (one row per date)
macro_wide as (
    select
        date,
        max(case when indicator = 'fed_funds_rate' then value end) as fed_funds_rate,
        max(case when indicator = 'cpi' then value end) as cpi,
        max(case when indicator = 'unemployment_rate' then value end) as unemployment_rate,
        max(case when indicator = 'yield_spread_10y2y' then value end) as yield_spread_10y2y,
        max(case when indicator = 'gdp' then value end) as gdp
    from macro_indicators
    group by date
),

-- Forward-fill nulls so monthly/quarterly values propagate to daily dates
macro_filled as (
    select
        date,
        coalesce(fed_funds_rate, lag(fed_funds_rate) over (order by date)) as fed_funds_rate,
        coalesce(cpi, lag(cpi) over (order by date)) as cpi,
        coalesce(unemployment_rate, lag(unemployment_rate) over (order by date)) as unemployment_rate,
        coalesce(yield_spread_10y2y, lag(yield_spread_10y2y) over (order by date)) as yield_spread_10y2y,
        coalesce(gdp, lag(gdp) over (order by date)) as gdp
    from macro_wide
),

-- Join sector prices to nearest available macro observation date
joined as (
    select
        sp.symbol,
        sp.sector,
        sp.date,
        sp.open,
        sp.high,
        sp.low,
        sp.close,
        sp.volume,
        sp.daily_return_pct,
        mf.fed_funds_rate,
        mf.cpi,
        mf.unemployment_rate,
        mf.yield_spread_10y2y,
        mf.gdp
    from sector_prices sp
    left join macro_filled mf
        on mf.date = (
            -- For each trading day, find the most recent macro date on or before it
            select max(m.date)
            from macro_filled m
            where m.date <= sp.date
        )
)

select * from joined