with base as (
    select * from {{ ref('int_sector_macro_joined') }}
),

-- Classify macro regime based on fed funds rate and yield spread
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

-- Add 30-day rolling average return per sector
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
        avg(daily_return_pct) over (
            partition by symbol
            order by date
            rows between 29 preceding and current row
        ) as rolling_30d_avg_return
    from with_regime
)

select * from final