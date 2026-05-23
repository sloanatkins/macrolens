{#
  mart_sector_performance
  =======================
  Final analytics-ready table consumed directly by the Streamlit dashboard.
  Adds macro regime classification and 30-day rolling average return to
  the joined sector + macro dataset.

  Source: int_sector_macro_joined

  Transformations:

  Step 1 — with_regime:
    Classifies each trading day into one of five macro regimes based on
    the Fed Funds Rate and 10Y-2Y yield spread:

    Regime        | Fed Rate  | Yield Spread
    --------------|-----------|-------------
    restrictive   | >= 5.0%   | < 0
    tightening    | >= 3.5%   | >= 0
    expansionary  | < 2.0%    | >= 0
    recovery      | < 2.0%    | < 0
    neutral       | all other conditions

  Step 2 — final:
    Adds rolling_30d_avg_return using a 30-row window function partitioned
    by symbol. This smooths daily volatility and makes sector momentum
    trends visible in the dashboard line chart.

  Materialized as: table (not view — queried directly by dashboard)
#}

with base as (
    select * from {{ ref('int_sector_macro_joined') }}
),

-- Classify each trading day into a macro regime based on Fed rate and yield spread
with_regime as (
    select
        *,
        case
            when fed_funds_rate >= 5.0 and yield_spread_10y2y < 0 then 'restrictive'
            when fed_funds_rate >= 3.5 and yield_spread_10y2y >= 0 then 'tightening'
            when fed_funds_rate < 2.0 and yield_spread_10y2y >= 0 then 'expansionary'
            when fed_funds_rate < 2.0 and yield_spread_10y2y < 0 then 'recovery'
            else 'neutral'
        end as macro_regime
    from base
),

-- Add 30-day rolling average return per sector using a window function
final as (
    select
        symbol,
        sector,
        date,
        open,
        high,
        low,
        close,
        volume,
        daily_return_pct,
        fed_funds_rate,
        cpi,
        unemployment_rate,
        yield_spread_10y2y,
        gdp,
        macro_regime,
        -- Rolling 30-day average smooths daily noise and surfaces momentum trends
        avg(daily_return_pct) over (
            partition by symbol       -- calculated independently per sector
            order by date
            rows between 29 preceding and current row
        ) as rolling_30d_avg_return
    from with_regime
)

select * from final