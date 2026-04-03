with daily as (
    select
        date,
        round(avg(temperature_c), 2)      as avg_temperature_c,
        round(min(temperature_c), 2)      as min_temperature_c,
        round(max(temperature_c), 2)      as max_temperature_c,
        round(sum(precipitation_mm), 2)   as total_precipitation_mm,
        round(avg(humidity_pct), 2)       as avg_humidity_pct,
        round(avg(pressure_hpa), 2)       as avg_pressure_hpa,
        round(avg(pm2_5), 2)              as avg_pm2_5,
        round(avg(ozone), 2)              as avg_ozone,
        max(us_aqi)                       as max_us_aqi
    from {{ ref('stg_weather_hourly') }}
    group by date
    order by date
)

select * from daily
