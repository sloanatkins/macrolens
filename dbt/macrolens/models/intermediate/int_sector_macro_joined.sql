with sector_prices as (
    select * from {{ ref('stg_sector_prices') }}
),

macro_indicators as (
    select * from {{ ref('stg_macro_indicators') }}
),

-- Pivot macro indicators to wide format for joining
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

-- Join sector prices to nearest macro date
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
        mw.fed_funds_rate,
        mw.cpi,
        mw.unemployment_rate,
        mw.yield_spread_10y2y,
        mw.gdp
    from sector_prices sp
    left join macro_wide mw
        on mw.date = (
            select max(m.date)
            from macro_wide m
            where m.date <= sp.date
        )
)

select * from joined