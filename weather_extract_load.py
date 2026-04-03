import requests
import pandas as pd
import duckdb
from datetime import date, timedelta

# --- Config ---
DUCKDB_FILE = "reports/sources/breathe/breathe_dev.duckdb"
LAT = 44.9778
LON = -93.2650
WEATHER_API = "https://archive-api.open-meteo.com/v1/archive"
AIR_QUALITY_API = "https://air-quality-api.open-meteo.com/v1/air-quality"


def ensure_table(con):
    """Create raw_weather_hourly if it doesn't exist."""
    con.execute("""
        CREATE TABLE IF NOT EXISTS raw_weather_hourly (
            timestamp TIMESTAMP PRIMARY KEY,
            temperature_c DOUBLE,
            humidity_pct DOUBLE,
            precipitation_mm DOUBLE,
            pressure_hpa DOUBLE,
            pm2_5 DOUBLE,
            ozone DOUBLE,
            us_aqi INTEGER
        )
    """)


def get_date_range(con):
    """
    Returns (start_date, end_date) to fetch, as date objects.
    - Incremental: day after last loaded row up to yesterday.
    - Backfill: earliest raw_breathe date up to yesterday.
    - Already current: returns (None, None).
    """
    yesterday = date.today() - timedelta(days=1)

    result = con.execute(
        "SELECT MAX(timestamp::DATE) FROM raw_weather_hourly"
    ).fetchone()[0]

    if result is not None:
        start_date = result + timedelta(days=1)
        if start_date > yesterday:
            print("Weather data is already up to date.")
            return None, None
        return start_date, yesterday

    # No weather data yet — backfill from first symptom date
    result = con.execute(
        "SELECT MIN(timestamp::DATE) FROM raw_breathe"
    ).fetchone()[0]
    if result is None:
        raise ValueError(
            "No data in raw_breathe — cannot determine backfill start date."
        )
    return result, yesterday


def fetch_weather(start_date, end_date):
    """Fetch hourly weather data from Open-Meteo archive API."""
    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,surface_pressure",
        "timezone": "America/Chicago",
        "temperature_unit": "celsius",
    }
    resp = requests.get(WEATHER_API, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()["hourly"]

    return pd.DataFrame({
        "timestamp": pd.to_datetime(data["time"]),
        "temperature_c": data["temperature_2m"],
        "humidity_pct": data["relative_humidity_2m"],
        "precipitation_mm": data["precipitation"],
        "pressure_hpa": data["surface_pressure"],
    })


def fetch_air_quality(start_date, end_date):
    """
    Fetch hourly air quality data from Open-Meteo.
    Returns None (with a warning) if the API fails or data is unavailable.
    """
    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "hourly": "pm2_5,ozone,us_aqi",
        "timezone": "America/Chicago",
    }
    try:
        resp = requests.get(AIR_QUALITY_API, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()["hourly"]
        return pd.DataFrame({
            "timestamp": pd.to_datetime(data["time"]),
            "pm2_5": data["pm2_5"],
            "ozone": data["ozone"],
            "us_aqi": data["us_aqi"],
        })
    except Exception as e:
        print(
            f"Warning: air quality data unavailable for {start_date} to {end_date}: {e}"
        )
        return None


def load_to_duckdb(con, weather_df, air_quality_df, start_date, end_date):
    """
    Merge weather and air quality DataFrames, delete the date range, and re-insert.
    Passing None for air_quality_df fills those columns with NULL.
    """
    if air_quality_df is not None:
        df = weather_df.merge(air_quality_df, on="timestamp", how="left")
    else:
        df = weather_df.copy()
        df["pm2_5"] = None
        df["ozone"] = None
        df["us_aqi"] = None

    con.execute("""
        DELETE FROM raw_weather_hourly
        WHERE timestamp::DATE >= ? AND timestamp::DATE <= ?
    """, [start_date, end_date])

    con.execute("""
        INSERT INTO raw_weather_hourly
            (timestamp, temperature_c, humidity_pct, precipitation_mm, pressure_hpa,
             pm2_5, ozone, us_aqi)
        SELECT timestamp, temperature_c, humidity_pct, precipitation_mm, pressure_hpa,
               pm2_5, ozone, us_aqi
        FROM df
    """)
    print(f"Loaded {len(df)} rows into raw_weather_hourly ({start_date} to {end_date})")


if __name__ == "__main__":
    pass
