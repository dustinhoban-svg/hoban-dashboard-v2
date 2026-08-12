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
            vix REAL,
            real_5y REAL,
            real_10y REAL,
            real_20y REAL,
            real_30y REAL,
            breakeven_5y REAL,
            ccc_spread REAL,
            move_index REAL,
            hyg REAL,
            jnk REAL,
            vvix REAL,
            mstr REAL,
            dxy REAL,
            btc REAL,
            sp500 REAL,
            nasdaq REAL
        )
    """)
    # Add any columns missing from an older table version, so existing tables upgrade automatically
    new_columns = {
        "real_5y": "REAL", "real_10y": "REAL", "real_20y": "REAL", "real_30y": "REAL",
        "breakeven_5y": "REAL", "ccc_spread": "REAL", "move_index": "REAL",
        "hyg": "REAL", "jnk": "REAL", "vvix": "REAL", "mstr": "REAL",
        "dxy": "REAL", "btc": "REAL", "sp500": "REAL", "nasdaq": "REAL"
    }
    for col, coltype in new_columns.items():
        try:
            cur.execute(f"ALTER TABLE snapshots ADD COLUMN IF NOT EXISTS {col} {coltype}")
        except Exception as e:
            print(f"Column add skipped for {col}: {e}")
    conn.commit()
    cur.close()
    conn.close()

def to_float(x):
    return float(x) if x is not None else None

def save_daily_snapshot(fred_data, market_data):
    today = date.today()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM snapshots WHERE snapshot_date = %s", (today,))
    existing = cur.fetchone()

    if existing:
        cur.close()
        conn.close()
        return False  # already saved today

    cur.execute("""
        INSERT INTO snapshots (
            snapshot_date, fed_funds, treasury_10y, treasury_2y, fed_balance_sheet,
            reverse_repo, tga, hy_credit_spread, cpi, breakeven_inflation,
            unemployment, jobless_claims, vix, real_5y, real_10y, real_20y, real_30y,
            breakeven_5y, ccc_spread, move_index, hyg, jnk, vvix, mstr, dxy, btc,
            sp500, nasdaq
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
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
        to_float(market_data.get("VIX")),
        to_float(fred_data.get("5Y Real Rate")),
        to_float(fred_data.get("10Y Real Rate")),
        to_float(fred_data.get("20Y Real Rate")),
        to_float(fred_data.get("30Y Real Rate")),
        to_float(fred_data.get("5Y Breakeven Inflation")),
        to_float(fred_data.get("CCC Credit Spread")),
        to_float(market_data.get("MOVE Index")),
        to_float(market_data.get("HYG")),
        to_float(market_data.get("JNK")),
        to_float(market_data.get("VVIX")),
        to_float(market_data.get("MSTR")),
        to_float(market_data.get("Dollar Index")),
        to_float(market_data.get("Bitcoin")),
        to_float(market_data.get("S&P 500")),
        to_float(market_data.get("Nasdaq"))
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
