with rounds as (
    select
        session_id,
        min(logged_at)              as logged_at,
        count(*)                    as round_count,
        max(severity_level)         as max_retention_s,
        round(avg(severity_level), 1) as avg_retention_s,
        sum(severity_level)         as total_retention_s,
        max(case when severity_label = 'round_1' then note end) as note
    from {{ ref('stg_breathe') }}
    where entry_type = 'wim_hof'
    group by session_id
)

select * from rounds
order by logged_at
