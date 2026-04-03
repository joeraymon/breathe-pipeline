# Weather + Air Quality Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `weather_extract_load.py` script that fetches hourly weather and air quality data from Open-Meteo into DuckDB, plus dbt models that produce a daily mart joinable to existing symptom tables.

**Architecture:** A standalone Python script manages its own date range (backfill from first symptom date, or incremental from last loaded date), makes two Open-Meteo API calls (weather + air quality), merges the results, and loads into a `raw_weather_hourly` DuckDB table. Two dbt models — a staging view and a daily mart — sit on top of that table.

**Tech Stack:** Python, `requests`, `pandas`, `duckdb`, dbt (DuckDB adapter), Open-Meteo archive API, pytest

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `weather_extract_load.py` | Create | Main EL script — API fetch + DuckDB load |
| `tests/test_weather_extract_load.py` | Create | pytest tests for all script functions |
| `requirements.txt` | Create | Pin Python dependencies |
| `breathe/models/staging/stg_weather_hourly.sql` | Create | Staging view over `raw_weather_hourly` |
| `breathe/models/marts/weather_daily.sql` | Create | Daily aggregate mart, joinable on `date` |

---

## Task 1: Add `requests` to dependencies

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Create `requirements.txt`**

```
gspread
pandas
duckdb
google-auth
requests
pytest
```

- [ ] **Step 2: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: no errors, `requests` and `pytest` available.

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "add requirements.txt with requests and pytest"
```

---

## Task 2: Write tests for `get_date_range`

**Files:**
- Create: `tests/test_weather_extract_load.py`

This function determines whether to backfill (from earliest `raw_breathe` date) or run incrementally (from day after last loaded weather row). Write the tests before the implementation.

- [ ] **Step 1: Create `tests/test_weather_extract_load.py` with fixtures and `get_date_range` tests**

```python
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
```

- [ ] **Step 2: Run tests to confirm they fail (module not found)**

```bash
pytest tests/test_weather_extract_load.py -v
```

Expected: `ModuleNotFoundError: No module named 'weather_extract_load'`

---

## Task 3: Implement script skeleton + `ensure_table` + `get_date_range`

**Files:**
- Create: `weather_extract_load.py`

- [ ] **Step 1: Create `weather_extract_load.py`**

```python
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
```

- [ ] **Step 2: Run `get_date_range` tests**

```bash
pytest tests/test_weather_extract_load.py::test_get_date_range_backfill tests/test_weather_extract_load.py::test_get_date_range_incremental tests/test_weather_extract_load.py::test_get_date_range_already_current -v
```

Expected: all 3 PASS

- [ ] **Step 3: Commit**

```bash
git add weather_extract_load.py tests/test_weather_extract_load.py
git commit -m "add weather script skeleton with ensure_table and get_date_range"
```

---

## Task 4: Write and implement `fetch_weather`

**Files:**
- Modify: `tests/test_weather_extract_load.py`
- Modify: `weather_extract_load.py`

- [ ] **Step 1: Add `fetch_weather` test to `tests/test_weather_extract_load.py`**

Add after the `test_get_date_range_already_current` test:

```python
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
```

- [ ] **Step 2: Run to confirm it fails**

```bash
pytest tests/test_weather_extract_load.py::test_fetch_weather -v
```

Expected: FAIL with `AttributeError: module 'weather_extract_load' has no attribute 'fetch_weather'`

- [ ] **Step 3: Add `fetch_weather` to `weather_extract_load.py`**

Add after `get_date_range`:

```python
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
```

- [ ] **Step 4: Run test to confirm it passes**

```bash
pytest tests/test_weather_extract_load.py::test_fetch_weather -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add weather_extract_load.py tests/test_weather_extract_load.py
git commit -m "add fetch_weather with tests"
```

---

## Task 5: Write and implement `fetch_air_quality`

**Files:**
- Modify: `tests/test_weather_extract_load.py`
- Modify: `weather_extract_load.py`

- [ ] **Step 1: Add `fetch_air_quality` tests to `tests/test_weather_extract_load.py`**

Add after `test_fetch_weather`:

```python
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
```

- [ ] **Step 2: Run to confirm they fail**

```bash
pytest tests/test_weather_extract_load.py::test_fetch_air_quality tests/test_weather_extract_load.py::test_fetch_air_quality_returns_none_on_error -v
```

Expected: both FAIL with `AttributeError`

- [ ] **Step 3: Add `fetch_air_quality` to `weather_extract_load.py`**

Add after `fetch_weather`:

```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_weather_extract_load.py::test_fetch_air_quality tests/test_weather_extract_load.py::test_fetch_air_quality_returns_none_on_error -v
```

Expected: both PASS

- [ ] **Step 5: Commit**

```bash
git add weather_extract_load.py tests/test_weather_extract_load.py
git commit -m "add fetch_air_quality with graceful failure handling"
```

---

## Task 6: Write and implement `load_to_duckdb`

**Files:**
- Modify: `tests/test_weather_extract_load.py`
- Modify: `weather_extract_load.py`

- [ ] **Step 1: Add `load_to_duckdb` tests to `tests/test_weather_extract_load.py`**

Add after `test_fetch_air_quality_returns_none_on_error`:

```python
@pytest.fixture
def weather_df():
    return pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-06-01T00:00", "2024-06-01T01:00"]),
        "temperature_c": [18.5, 17.9],
        "humidity_pct": [65.0, 67.0],
        "precipitation_mm": [0.0, 0.1],
        "pressure_hpa": [1013.0, 1012.8],
    })


@pytest.fixture
def aq_df():
    return pd.DataFrame({
        "timestamp": pd.to_datetime(["2024-06-01T00:00", "2024-06-01T01:00"]),
        "pm2_5": [8.2, 9.1],
        "ozone": [55.0, 54.0],
        "us_aqi": [35, 38],
    })


def test_load_to_duckdb_with_air_quality(con, weather_df, aq_df):
    """Merges weather + air quality and inserts all columns."""
    wel.ensure_table(con)
    wel.load_to_duckdb(con, weather_df, aq_df, date(2024, 6, 1), date(2024, 6, 1))
    count = con.execute("SELECT COUNT(*) FROM raw_weather_hourly").fetchone()[0]
    assert count == 2
    row = con.execute(
        "SELECT pm2_5, ozone, us_aqi FROM raw_weather_hourly ORDER BY timestamp LIMIT 1"
    ).fetchone()
    assert row[0] == 8.2
    assert row[2] == 35


def test_load_to_duckdb_without_air_quality(con, weather_df):
    """When air quality fetch failed, air quality columns are NULL."""
    wel.ensure_table(con)
    wel.load_to_duckdb(con, weather_df, None, date(2024, 6, 1), date(2024, 6, 1))
    row = con.execute(
        "SELECT pm2_5, ozone, us_aqi FROM raw_weather_hourly LIMIT 1"
    ).fetchone()
    assert row[0] is None
    assert row[1] is None
    assert row[2] is None


def test_load_to_duckdb_is_idempotent(con, weather_df):
    """Re-loading the same date range does not duplicate rows."""
    wel.ensure_table(con)
    wel.load_to_duckdb(con, weather_df, None, date(2024, 6, 1), date(2024, 6, 1))
    wel.load_to_duckdb(con, weather_df, None, date(2024, 6, 1), date(2024, 6, 1))
    count = con.execute("SELECT COUNT(*) FROM raw_weather_hourly").fetchone()[0]
    assert count == 2
```

- [ ] **Step 2: Run to confirm they fail**

```bash
pytest tests/test_weather_extract_load.py::test_load_to_duckdb_with_air_quality tests/test_weather_extract_load.py::test_load_to_duckdb_without_air_quality tests/test_weather_extract_load.py::test_load_to_duckdb_is_idempotent -v
```

Expected: all FAIL with `AttributeError`

- [ ] **Step 3: Add `load_to_duckdb` to `weather_extract_load.py`**

Add after `fetch_air_quality`:

```python
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

    con.execute("INSERT INTO raw_weather_hourly SELECT * FROM df")
    print(f"Loaded {len(df)} rows into raw_weather_hourly ({start_date} to {end_date})")
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_weather_extract_load.py::test_load_to_duckdb_with_air_quality tests/test_weather_extract_load.py::test_load_to_duckdb_without_air_quality tests/test_weather_extract_load.py::test_load_to_duckdb_is_idempotent -v
```

Expected: all 3 PASS

- [ ] **Step 5: Commit**

```bash
git add weather_extract_load.py tests/test_weather_extract_load.py
git commit -m "add load_to_duckdb with idempotent date-range replacement"
```

---

## Task 7: Wire up `main()` and run full test suite

**Files:**
- Modify: `weather_extract_load.py`

- [ ] **Step 1: Replace the `pass` in `__main__` block with a full `main()` function**

Replace the bottom of `weather_extract_load.py`:

```python
def main():
    con = duckdb.connect(DUCKDB_FILE)
    ensure_table(con)

    start_date, end_date = get_date_range(con)
    if start_date is None:
        con.close()
        return

    print(f"Fetching weather + air quality data from {start_date} to {end_date}...")
    weather_df = fetch_weather(start_date, end_date)
    air_quality_df = fetch_air_quality(start_date, end_date)

    load_to_duckdb(con, weather_df, air_quality_df, start_date, end_date)
    con.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full test suite**

```bash
pytest tests/test_weather_extract_load.py -v
```

Expected: all 10 tests PASS

- [ ] **Step 3: Do a live manual run**

```bash
python weather_extract_load.py
```

Expected output:
```
Fetching weather + air quality data from YYYY-MM-DD to YYYY-MM-DD...
Loaded NNNN rows into raw_weather_hourly (YYYY-MM-DD to YYYY-MM-DD)
```

Verify rows loaded:

```bash
python -c "import duckdb; con = duckdb.connect('reports/sources/breathe/breathe_dev.duckdb'); print(con.execute('SELECT MIN(timestamp), MAX(timestamp), COUNT(*) FROM raw_weather_hourly').fetchone())"
```

Expected: a row count in the thousands, min/max timestamps spanning from first symptom date to yesterday.

- [ ] **Step 4: Commit**

```bash
git add weather_extract_load.py
git commit -m "wire up main() for weather extract-load script"
```

---

## Task 8: Add dbt staging model `stg_weather_hourly`

**Files:**
- Create: `breathe/models/staging/stg_weather_hourly.sql`

- [ ] **Step 1: Create `breathe/models/staging/stg_weather_hourly.sql`**

```sql
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
```

- [ ] **Step 2: Run the model**

```bash
cd breathe && dbt run -s stg_weather_hourly
```

Expected: `1 of 1 OK created sql view model ... stg_weather_hourly`

- [ ] **Step 3: Commit**

```bash
git add breathe/models/staging/stg_weather_hourly.sql
git commit -m "add stg_weather_hourly staging view"
```

---

## Task 9: Add dbt mart `weather_daily`

**Files:**
- Create: `breathe/models/marts/weather_daily.sql`

- [ ] **Step 1: Create `breathe/models/marts/weather_daily.sql`**

```sql
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
```

- [ ] **Step 2: Run the model**

```bash
cd breathe && dbt run -s weather_daily
```

Expected: `1 of 1 OK created sql table model ... weather_daily`

- [ ] **Step 3: Verify the join to symptom data works**

```bash
python -c "
import duckdb
con = duckdb.connect('reports/sources/breathe/breathe_dev.duckdb')
result = con.execute('''
    SELECT sd.severity_date, sd.avg_severity, wd.avg_temperature_c, wd.max_us_aqi
    FROM severity_daily sd
    LEFT JOIN weather_daily wd ON sd.severity_date = wd.date
    ORDER BY sd.severity_date
    LIMIT 5
''').fetchdf()
print(result)
con.close()
"
```

Expected: a dataframe with severity and weather columns side by side, non-null weather values where dates overlap.

- [ ] **Step 4: Run full dbt project**

```bash
cd breathe && dbt run
```

Expected: all models pass.

- [ ] **Step 5: Commit**

```bash
git add breathe/models/marts/weather_daily.sql
git commit -m "add weather_daily mart joinable to severity_daily on date"
```
