from fredapi import Fred
from config.settings import FRED_API_KEY


fred = Fred(api_key=FRED_API_KEY)


def get_fred_data():

    data = {}

    indicators = {
        "Fed Funds Rate": "FEDFUNDS",
        "10Y Treasury": "DGS10",
        "2Y Treasury": "DGS2",
        "Fed Balance Sheet": "WALCL",
        "Reverse Repo": "RRPONTSYD",
        "Treasury General Account": "WTREGEN",
        "High Yield Credit Spread": "BAMLH0A0HYM2",
        "CPI": "CPIAUCSL",
        "10Y Breakeven Inflation": "T10YIE",
        "Unemployment Rate": "UNRATE",
        "Initial Jobless Claims": "ICSA",
        "5Y Real Rate": "DFII5",
        "10Y Real Rate": "DFII10",
        "20Y Real Rate": "DFII20",
        "30Y Real Rate": "DFII30",
        "5Y Breakeven Inflation": "T5YIE"    
}
    for name, series in indicators.items():
        try:
            value = fred.get_series(series).dropna().iloc[-1]
            data[name] = value
        except Exception:
            data[name] = None

    return data

def get_fred_history(series_id, start_date=None, end_date=None):
    """
    Returns a pandas Series of historical values for a given FRED series ID,
    optionally bounded by start_date/end_date (as 'YYYY-MM-DD' strings or None).
    """
    data = fred.get_series(series_id, observation_start=start_date, observation_end=end_date)
    return data.dropna()
