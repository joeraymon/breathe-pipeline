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
