with weekly as (
    select
        date_trunc('week', logged_at::date) as week_start,
        round(avg(severity_level), 2) as avg_severity,
        count(*) as log_count,
        max(severity_level) as max_severity,
        sum(case when severity_label = 'Clear' then 1 else 0 end) as clear_days,
        sum(case when severity_label = 'Mild' then 1 else 0 end) as mild_days,
        sum(case when severity_label = 'Moderate' then 1 else 0 end) as moderate_days,
        sum(case when severity_label = 'Extreme' then 1 else 0 end) as extreme_days
    from {{ ref('severity_events') }}
    group by date_trunc('week', logged_at::date)
    order by week_start
)

select * from weekly