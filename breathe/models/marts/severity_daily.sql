with daily as (
    select
        logged_at::date as severity_date,
        round(avg(severity_level), 2) as avg_severity,
        count(*) as log_count,
        max(severity_level) as max_severity,
        min(severity_level) as min_severity
    from {{ ref('severity_events') }}
    group by logged_at::date
    order by severity_date
)

select * from daily