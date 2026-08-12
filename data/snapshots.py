import psycopg2
from datetime import date
from config.settings import DATABASE_URL

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            snapshot_date DATE PRIMARY KEY,
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
    cur.close()
    conn.close()

def save_daily_snapshot(fred_data, vix_value):
    today = date.today()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM snapshots WHERE snapshot_date = %s", (today,))
    existing = cur.fetchone()

    if existing:
        cur.close()
        conn.close()
        return False  # already saved today

    def to_float(x):
        return float(x) if x is not None else None

    cur.execute("""
        INSERT INTO snapshots VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        today,
        to_float(fred_data.get("Fed Funds Rate")),
        to_float(fred_data.get("10Y Treasury")),
        to_float(fred_data.get("2Y Treasury")),
        to_float(fred_data.get("Fed Balance Sheet")),
        to_float(fred_data.get("Reverse Repo")),
        to_float(fred_data.get("Treasury General Account")),
        to_float(fred_data.get("High Yield Credit Spread")),
        to_float(fred_data.get("CPI")),
        to_float(fred_data.get("10Y Breakeven Inflation")),
        to_float(fred_data.get("Unemployment Rate")),
        to_float(fred_data.get("Initial Jobless Claims")),
        to_float(vix_value)
    ))
    conn.commit()
    cur.close()
    conn.close()
    return True

def load_snapshot_history():
    import pandas as pd
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM snapshots ORDER BY snapshot_date", conn)
    conn.close()
    return df
