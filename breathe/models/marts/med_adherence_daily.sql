with med_events as (
    select
        logged_at::date as date,
        entry_type
    from {{ ref('stg_breathe') }}
    where entry_type in ('preventative_inhaler', 'rescue', 'zyrtec', 'allergy_shot')
),

daily as (
    select
        date,
        count(case when entry_type = 'preventative_inhaler' then 1 end) as preventative_inhaler_count,
        count(case when entry_type = 'rescue'               then 1 end) as rescue_count,
        count(case when entry_type = 'zyrtec'               then 1 end) as zyrtec_count,
        count(case when entry_type = 'allergy_shot'         then 1 end) as allergy_shot_count
    from med_events
    group by date
)

select * from daily
order by date
