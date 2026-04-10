with summary as (
    select
        coalesce(s.severity_date, m.date, w.date) as date,
        s.avg_severity,
        s.max_severity,
        s.log_count                                as severity_log_count,
        m.preventative_inhaler_count,
        m.rescue_count,
        m.zyrtec_count,
        m.allergy_shot_count,
        w.avg_temperature_c,
        w.avg_humidity_pct,
        w.avg_pm2_5,
        w.max_us_aqi
    from {{ ref('severity_daily') }} s
    full outer join {{ ref('med_adherence_daily') }} m
        on s.severity_date = m.date
    full outer join {{ ref('weather_daily') }} w
        on coalesce(s.severity_date, m.date) = w.date
)

select * from summary
order by date
