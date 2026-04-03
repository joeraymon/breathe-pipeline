with severity_events as (
    select
        logged_at,
        entry_type,
        severity_level,
        severity_label,
        note
    from {{ ref('stg_breathe') }}
    where entry_type = 'severity'
)

select * from severity_events