with inhaler_events as (
    select
        logged_at,
        entry_type,
        note
    from {{ ref('stg_breathe') }}
    where entry_type = 'rescue'
)

select * from inhaler_events