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


if __name__ == "__main__":
    pass
