# Weather + Air Quality Integration Design

**Date:** 2026-04-02  
**Scope:** Add nightly Open-Meteo weather and air quality data to the breathe-pipeline, joinable to daily symptom logs.

---

## Overview

A new Python script (`weather_extract_load.py`) fetches hourly weather and air quality data from Open-Meteo for Minneapolis, MN and loads it into DuckDB. Two dbt models transform the raw hourly data into a daily mart table joinable to existing symptom marts. Google Pollen API integration is explicitly out of scope and deferred to a future phase.

---

## Data Source

**Open-Meteo** — free, no API key required.

Two API endpoints, both using Minneapolis coordinates (`lat=44.9778, lon=-93.2650`):

- **Weather archive:** `https://archive-api.open-meteo.com/v1/archive`
  - Variables: `temperature_2m`, `relative_humidity_2m`, `precipitation`, `surface_pressure`
- **Air quality archive:** `https://air-quality-api.open-meteo.com/v1/air-quality`
  - Variables: `pm2_5`, `ozone`, `us_aqi`

Both endpoints return hourly data. Air quality archive availability is approximately 5 years back; weather archive goes further.

---

## Script: `weather_extract_load.py`

### Date Range Logic

The script is self-managing — no manual date arguments needed for normal operation:

- **First run (backfill):** queries `raw_breathe` for the earliest `logged_at` date, fetches from there to yesterday
- **Subsequent runs:** queries `raw_weather_hourly` for the most recent `timestamp`, fetches from the day after that to yesterday

This means re-running is always safe and gaps auto-heal on the next execution.

### Insert Strategy

`INSERT OR REPLACE` into `raw_weather_hourly` keyed on `timestamp`. Re-running the same date range is idempotent.

### Error Handling

- **Missing air quality data** (e.g., dates before archive coverage): insert `NULL` for air quality columns, log a warning, continue
- **API errors:** raise an exception with a descriptive message — no silent failures, no retries
- **Gap recovery:** if a nightly run fails, the next run automatically backfills the missed day

---

## Storage Schema

**Table: `raw_weather_hourly`** (DuckDB)

| Column | Type | Notes |
|---|---|---|
| `timestamp` | TIMESTAMP | Primary key, hour-precision UTC |
| `temperature_c` | DOUBLE | `temperature_2m` from API |
| `humidity_pct` | DOUBLE | `relative_humidity_2m` |
| `precipitation_mm` | DOUBLE | `precipitation` |
| `pressure_hpa` | DOUBLE | `surface_pressure` |
| `pm2_5` | DOUBLE | Nullable |
| `ozone` | DOUBLE | Nullable |
| `us_aqi` | INTEGER | Nullable, daily max used for correlation |

---

## dbt Models

### `stg_weather_hourly` (view, `models/staging/`)

Casts types and standardizes column names from `raw_weather_hourly`. Derives a `date` column (`timestamp::DATE`) for downstream joins.

### `weather_daily` (table, `models/marts/`)

Daily aggregates over `stg_weather_hourly`:

| Column | Aggregation |
|---|---|
| `date` | Group key |
| `avg_temperature_c` | AVG |
| `min_temperature_c` | MIN |
| `max_temperature_c` | MAX |
| `total_precipitation_mm` | SUM |
| `avg_humidity_pct` | AVG |
| `avg_pressure_hpa` | AVG |
| `avg_pm2_5` | AVG |
| `avg_ozone` | AVG |
| `max_us_aqi` | MAX |

### Join Pattern

`weather_daily.date` joins directly to `severity_daily.date` and `inhaler_usage_daily.date`:

```sql
SELECT *
FROM severity_daily sd
LEFT JOIN weather_daily wd ON sd.date = wd.date
```

---

## Scheduling

- **Now:** manual execution (`python weather_extract_load.py`)
- **Later:** GitHub Actions scheduled workflow (nightly, e.g. `0 6 * * *` UTC to capture previous day's finalized data)

The script requires no changes between manual and scheduled operation.

---

## Out of Scope

- Google Pollen API (deferred to a future phase as a separate source)
- Evidence dashboard changes (separate task)
- Retry logic (gap recovery via re-run is sufficient)
