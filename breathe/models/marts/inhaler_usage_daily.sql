with daily as (
    select
        logged_at::date as usage_date,
        count(*) as usage_count
    from {{ ref('inhaler_usage') }}
    group by logged_at::date
    order by usage_date
)

select * from daily