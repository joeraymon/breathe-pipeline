import pytest
from unittest.mock import patch, MagicMock
from datetime import date, timedelta
import pandas as pd
import duckdb
import weather_extract_load as wel


@pytest.fixture
def con():
    """In-memory DuckDB with a single raw_breathe row dated 2024-01-15."""
    c = duckdb.connect(":memory:")
    c.execute("""
        CREATE TABLE raw_breathe (
            timestamp TIMESTAMP,
            type VARCHAR,
            level INTEGER,
            label VARCHAR,
            note VARCHAR
        )
    """)
    c.execute(
        "INSERT INTO raw_breathe VALUES ('2024-01-15 09:00:00', 'severity', 2, 'mild', NULL)"
    )
    yield c
    c.close()


def test_get_date_range_backfill(con):
    """When raw_weather_hourly is empty, start date = earliest raw_breathe date."""
    wel.ensure_table(con)
    start, end = wel.get_date_range(con)
    assert start == date(2024, 1, 15)
    assert end == date.today() - timedelta(days=1)


def test_get_date_range_incremental(con):
    """When raw_weather_hourly has data, resume from the day after last loaded date."""
    wel.ensure_table(con)
    yesterday = date.today() - timedelta(days=1)
    last_loaded = yesterday - timedelta(days=3)
    con.execute(f"""
        INSERT INTO raw_weather_hourly VALUES
        ('{last_loaded}T12:00:00', 20.0, 60.0, 0.0, 1013.0, 5.0, 40.0, 30)
    """)
    start, end = wel.get_date_range(con)
    assert start == last_loaded + timedelta(days=1)
    assert end == yesterday


def test_get_date_range_already_current(con):
    """Returns (None, None) when weather data is already up to date."""
    wel.ensure_table(con)
    yesterday = date.today() - timedelta(days=1)
    con.execute(f"""
        INSERT INTO raw_weather_hourly VALUES
        ('{yesterday}T12:00:00', 20.0, 60.0, 0.0, 1013.0, 5.0, 40.0, 30)
    """)
    start, end = wel.get_date_range(con)
    assert start is None
    assert end is None


MOCK_WEATHER_RESPONSE = {
    "hourly": {
        "time": ["2024-06-01T00:00", "2024-06-01T01:00"],
        "temperature_2m": [18.5, 17.9],
        "relative_humidity_2m": [65.0, 67.0],
        "precipitation": [0.0, 0.1],
        "surface_pressure": [1013.0, 1012.8],
    }
}


def test_fetch_weather():
    with patch("weather_extract_load.requests.get") as mock_get:
        mock_get.return_value.json.return_value = MOCK_WEATHER_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        df = wel.fetch_weather(date(2024, 6, 1), date(2024, 6, 1))

    assert len(df) == 2
    assert list(df.columns) == [
        "timestamp", "temperature_c", "humidity_pct", "precipitation_mm", "pressure_hpa"
    ]
    assert df["temperature_c"].iloc[0] == 18.5
    assert df["humidity_pct"].iloc[1] == 67.0


MOCK_AQ_RESPONSE = {
    "hourly": {
        "time": ["2024-06-01T00:00", "2024-06-01T01:00"],
        "pm2_5": [8.2, 9.1],
        "ozone": [55.0, 54.0],
        "us_aqi": [35, 38],
    }
}


def test_fetch_air_quality():
    with patch("weather_extract_load.requests.get") as mock_get:
        mock_get.return_value.json.return_value = MOCK_AQ_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        df = wel.fetch_air_quality(date(2024, 6, 1), date(2024, 6, 1))

    assert len(df) == 2
    assert list(df.columns) == ["timestamp", "pm2_5", "ozone", "us_aqi"]
    assert df["us_aqi"].iloc[0] == 35


def test_fetch_air_quality_returns_none_on_error():
    """If the air quality API fails, return None (not an exception)."""
    with patch("weather_extract_load.requests.get") as mock_get:
        mock_get.return_value.raise_for_status.side_effect = Exception("503 error")
        result = wel.fetch_air_quality(date(2020, 1, 1), date(2020, 1, 1))

    assert result is None
