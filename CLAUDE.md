# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal health analytics pipeline for tracking asthma symptoms and rescue inhaler usage. Data flows from a mobile app through Google Sheets, into DuckDB via Python, transformed by dbt, and visualized with Evidence.

```
Breathe App → Google Sheets → extract_load.py → DuckDB → dbt → Evidence → Netlify
```

## Commands

### Python ETL
```bash
python extract_load.py   # Extract from Google Sheets, load into DuckDB
```

### dbt (run from `breathe/` directory)
```bash
dbt run                  # Build all models
dbt run -s stg_breathe   # Run a single model
dbt test                 # Run tests
dbt clean                # Remove target/ and dbt_packages/
```

### Evidence (run from `reports/` directory)
```bash
npm run dev              # Start dev server with live reload
npm run build            # Build static site
npm run sources          # Validate data sources
```

## Architecture

### Data Layers

**Staging** (`breathe/models/staging/`): `stg_breathe.sql` — casts types, renames columns, handles nulls from `raw_breathe` (the DuckDB table loaded by the Python script).

**Marts** (`breathe/models/marts/`): Two tracks built on `stg_breathe`:
- Severity track: `severity_events` → `severity_daily` / `severity_weekly`
- Inhaler track: `inhaler_usage` → `inhaler_usage_daily` / `inhaler_usage_weekly`

Staging materializes as **views**; marts materialize as **tables** (configured in `dbt_project.yml`).

### Databases
- `breathe.duckdb` — production
- `breathe_dev.duckdb` — development; also copied to `reports/sources/breathe/` for Evidence

### Evidence Reports (`reports/`)
Pages live in `reports/pages/` as `.md` files with embedded SQL components. The DuckDB source is configured in `reports/sources/breathe/connection.yaml`. Pre-written SQL queries for Evidence live alongside the connection config in `reports/sources/breathe/`.

### Credentials
`breathe-gcp-credentials.json` is gitignored — required for `extract_load.py` to authenticate with Google Sheets.
