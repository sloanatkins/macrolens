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
        round((close - open) / open * 100, 4) as daily_return_pct,
        ingested_at
    from source
    where close is not null
      and date is not null
)

select * from cleaned