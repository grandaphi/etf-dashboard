from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
import yfinance as yf
import pandas as pd
import numpy as np

app = FastAPI()

tickers = {
    'VGS': 'VGS.AX', 'VAS': 'VAS.AX', 'IVV': 'IVV.AX', 
    'HNDQ': 'HNDQ.AX', 'SMH': 'SMH', 'EMKT': 'EMKT.AX', 
    'GOAT': 'GOAT.AX', 'QUAL': 'QUAL.AX'
}

ticker_names = {
    'VGS': 'International', 'VAS': 'Aussie', 'IVV': 'S&P 500',
    'HNDQ': 'Nasdaq', 'SMH': 'Semiconductor', 'EMKT': 'Emerging',
    'GOAT': 'Moat', 'QUAL': 'Quality'
}

HORIZONS = ['1w', '1m', '3m', '6m', '12m', '2y', '3y', '5y', '10y', 'max']

def calculate_indicators(df):
    # Moving Average Envelope (20-day SMA, 2.5% and 5% bands)
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['Env_Upper_2.5'] = df['SMA_20'] * 1.025
    df['Env_Lower_2.5'] = df['SMA_20'] * 0.975
    df['Env_Upper_5'] = df['SMA_20'] * 1.05
    df['Env_Lower_5'] = df['SMA_20'] * 0.95

    # RSI (14-day)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD (12, 26, 9)
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['Hist'] = df['MACD'] - df['Signal']
    
    return df

def adjust_unrecorded_splits(df):
    # Yahoo omits some AU unit splits from its split history, so auto-adjust
    # leaves them in the series. Any surviving one-day move beyond 50% is
    # treated as a split and used to rescale the earlier prices.
    close = df['Close']
    ratio = close / close.shift(1)
    suspect = (ratio < 0.5) | (ratio > 2)

    if not suspect.any():
        return df

    factors = ratio.where(suspect, 1.0).fillna(1.0)
    scale = factors[::-1].cumprod()[::-1].shift(-1).fillna(1.0)
    df['Close'] = close * scale

    return df

def horizon_start_dates(index):
    end_date = index[-1]
    return {
        '1w': end_date - pd.DateOffset(weeks=1),
        '1m': end_date - pd.DateOffset(months=1),
        '3m': end_date - pd.DateOffset(months=3),
        '6m': end_date - pd.DateOffset(months=6),
        '12m': end_date - pd.DateOffset(years=1),
        '2y': end_date - pd.DateOffset(years=2),
        '3y': end_date - pd.DateOffset(years=3),
        '5y': end_date - pd.DateOffset(years=5),
        '10y': end_date - pd.DateOffset(years=10),
        'max': index[0]
    }

def calculate_heat(df):
    # Buy heat (0-100) from the latest valid bar. RSI and the envelope score
    # how deep the dip is, MACD scores the momentum turn. Not a recommendation.
    scores = {}

    rsi = df['RSI'].dropna()
    if not rsi.empty:
        # 30 and below is hot, 70 and above is cold, matching the guide lines.
        scores['rsi'] = float(np.clip((70 - rsi.iloc[-1]) / 0.4, 0, 100))

    env = df[['Close', 'SMA_20']].dropna()
    if not env.empty:
        deviation = (env['Close'].iloc[-1] - env['SMA_20'].iloc[-1]) / env['SMA_20'].iloc[-1]
        scores['env'] = float(np.clip(50 - (deviation / 0.05) * 50, 0, 100))

    hist = df['Hist'].dropna()
    if len(hist) >= 2:
        latest, prior = float(hist.iloc[-1]), float(hist.iloc[-2])
        crossed_up = latest >= 0 and bool((hist.tail(4).iloc[:-1] < 0).any())

        if latest >= 0:
            scores['macd'] = 100.0 if crossed_up else (85.0 if latest > prior else 60.0)
        else:
            scores['macd'] = 55.0 if latest > prior else 10.0

    return scores

def horizon_returns(close):
    last = float(close.iloc[-1])
    starts = horizon_start_dates(close.index)
    returns = {}

    for key in HORIZONS:
        window = close.loc[starts[key]:]
        if len(window) < 2:
            returns[key] = None
            continue
        first = float(window.iloc[0])
        returns[key] = (last - first) / first * 100

    return returns

@app.get("/api/data/{etf}/{horizon}")
def get_etf_data(etf: str, horizon: str):
    ticker_symbol = tickers.get(etf.upper(), "VGS.AX")
    df_raw = yf.download(ticker_symbol, period='max')

    if isinstance(df_raw.columns, pd.MultiIndex):
        df_raw.columns = df_raw.columns.get_level_values(0)

    df = calculate_indicators(adjust_unrecorded_splits(df_raw.copy()))

    horizon_map = horizon_start_dates(df.index)

    start_date = horizon_map.get(horizon.lower(), horizon_map['12m'])
    df_filtered = df.loc[start_date:].replace({np.nan: None})
    
    dates = df_filtered.index.strftime('%Y-%m-%d').tolist()
    
    return {
        "dates": dates,
        "price": df_filtered['Close'].tolist(),
        "sma20": df_filtered['SMA_20'].tolist(),
        "env_u25": df_filtered['Env_Upper_2.5'].tolist(),
        "env_l25": df_filtered['Env_Lower_2.5'].tolist(),
        "env_u5": df_filtered['Env_Upper_5'].tolist(),
        "env_l5": df_filtered['Env_Lower_5'].tolist(),
        "rsi": df_filtered['RSI'].tolist(),
        "macd": df_filtered['MACD'].tolist(),
        "signal": df_filtered['Signal'].tolist(),
        "hist": df_filtered['Hist'].tolist(),
        "heat": calculate_heat(df)
    }

@app.get("/api/overview")
def get_overview():
    raw = yf.download(list(tickers.values()), period='max', group_by='ticker')
    rows = []

    for etf, symbol in tickers.items():
        df_raw = raw[symbol] if isinstance(raw.columns, pd.MultiIndex) else raw
        df_raw = df_raw.dropna(how='all')

        if df_raw.empty:
            continue

        df = calculate_indicators(adjust_unrecorded_splits(df_raw.copy()))
        close = df['Close'].dropna()

        rows.append({
            "etf": etf,
            "name": ticker_names.get(etf, ''),
            "price": float(close.iloc[-1]),
            "heat": calculate_heat(df),
            "returns": horizon_returns(close)
        })

    return {"horizons": HORIZONS, "rows": rows}

@app.get("/manifest.json")
def manifest(): return FileResponse("manifest.json")

@app.get("/sw.js")
def sw(): return FileResponse("sw.js")

@app.get("/", response_class=HTMLResponse)
def index():
    with open("index.html", "r", encoding="utf-8") as f: return f.read()

@app.get("/overview", response_class=HTMLResponse)
def overview():
    with open("overview.html", "r", encoding="utf-8") as f: return f.read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
