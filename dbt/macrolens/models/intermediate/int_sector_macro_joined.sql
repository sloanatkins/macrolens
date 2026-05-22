with sector_prices as (
    select * from {{ ref('stg_sector_prices') }}
),

macro_indicators as (
    select * from {{ ref('stg_macro_indicators') }}
),

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
            select max(m.date)
            from macro_filled m
            where m.date <= sp.date
        )
)

select * from joined