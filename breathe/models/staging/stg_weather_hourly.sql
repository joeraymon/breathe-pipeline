with source as (
    select * from raw_weather_hourly
),

renamed as (
    select
        timestamp                   as logged_at,
        timestamp::date             as date,
        temperature_c,
        humidity_pct,
        precipitation_mm,
        pressure_hpa,
        pm2_5,
        ozone,
        us_aqi
    from source
)

select * from renamed
