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
    where value is not null
      and date is not null
)

select * from cleaned