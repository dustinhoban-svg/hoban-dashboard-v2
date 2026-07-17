import sqlite3
from datetime import date

DB_PATH = "snapshots.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            snapshot_date TEXT PRIMARY KEY,
            fed_funds REAL,
            treasury_10y REAL,
            treasury_2y REAL,
            fed_balance_sheet REAL,
            reverse_repo REAL,
            tga REAL,
            hy_credit_spread REAL,
            cpi REAL,
            breakeven_inflation REAL,
            unemployment REAL,
            jobless_claims REAL,
            vix REAL
        )
    """)
    conn.commit()
    conn.close()

def save_daily_snapshot(fred_data, vix_value):
    today = str(date.today())
    conn = sqlite3.connect(DB_PATH)
    existing = conn.execute(
        "SELECT 1 FROM snapshots WHERE snapshot_date = ?", (today,)
    ).fetchone()

    if existing:
        conn.close()
        return False  # already saved today

    conn.execute("""
        INSERT INTO snapshots VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        today,
        fred_data.get("Fed Funds Rate"),
        fred_data.get("10Y Treasury"),
        fred_data.get("2Y Treasury"),
        fred_data.get("Fed Balance Sheet"),
        fred_data.get("Reverse Repo"),
        fred_data.get("Treasury General Account"),
        fred_data.get("High Yield Credit Spread"),
        fred_data.get("CPI"),
        fred_data.get("10Y Breakeven Inflation"),
        fred_data.get("Unemployment Rate"),
        fred_data.get("Initial Jobless Claims"),
        vix_value
    ))
    conn.commit()
    conn.close()
    return True

def load_snapshot_history():
    import pandas as pd
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM snapshots ORDER BY snapshot_date", conn)
    conn.close()
    return df
