import gspread
import pandas as pd
import duckdb
from google.oauth2.service_account import Credentials

# --- Config ---
CREDENTIALS_FILE = "breathe-gcp-credentials.json"
SHEET_NAME = "Asthma"  # update this to match your exact sheet name
TABLE_NAME = "raw_breathe"
DUCKDB_FILE = "reports/sources/breathe/breathe_dev.duckdb"

# --- Auth ---
scopes = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]

creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
client = gspread.authorize(creds)

# --- Extract ---
sheet = client.open(SHEET_NAME).sheet1
rows = sheet.get_all_records()

# --- Load to dataframe ---
df = pd.DataFrame(rows)
print(f"Extracted {len(df)} rows from Google Sheets")
print(df.head())

# --- Load to DuckDB ---
con = duckdb.connect(DUCKDB_FILE)
con.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        timestamp TIMESTAMP,
        type VARCHAR,
        level INTEGER,
        label VARCHAR,
        note VARCHAR
    )
""")

# Convert empty strings to None before inserting
df['level'] = pd.to_numeric(df['level'], errors='coerce')

con.execute(f"DELETE FROM {TABLE_NAME}")
con.execute(f"INSERT INTO {TABLE_NAME} (timestamp, type, level, label, note) SELECT timestamp, type, level, label, note FROM df")
print(f"Loaded {len(df)} rows into {TABLE_NAME}")
con.close()