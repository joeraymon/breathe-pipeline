with weekly as (
    select
        date_trunc('week', usage_date) as week_start,
        sum(usage_count) as weekly_usage_count
    from {{ ref('inhaler_usage_daily') }}
    group by date_trunc('week', usage_date)
    order by week_start
)

select * from weekly