import yfinance as yf


def get_market_data():

    symbols = {
        "S&P 500": "^GSPC",
        "Nasdaq": "^IXIC",
        "Bitcoin": "BTC-USD",
        "VIX": "^VIX",
        "10-Year Yield": "^TNX",
        "Dollar Index": "DX-Y.NYB",
        "MOVE Index": "^MOVE",
        "HYG": "HYG",
        "JNK": "JNK",
        "VVIX": "^VVIX",
        "MSTR": "MSTR"
    }

    market = {}

    for name, symbol in symbols.items():
        try:
            data = yf.Ticker(symbol)
            price = data.history(period="1d")["Close"].iloc[-1]
            market[name] = price

        except Exception as e:
            print(f"Market data error for {name} ({symbol}): {e}")
            market[name] = None

    return market
