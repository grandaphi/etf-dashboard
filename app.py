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

@app.get("/api/data/{etf}/{horizon}")
def get_etf_data(etf: str, horizon: str):
    ticker_symbol = tickers.get(etf.upper(), "VGS.AX")
    df_raw = yf.download(ticker_symbol, period='max')
    
    if isinstance(df_raw.columns, pd.MultiIndex):
        df_raw.columns = df_raw.columns.get_level_values(0)
        
    df = calculate_indicators(df_raw.copy())
    
    end_date = df.index[-1]
    horizon_map = {
        '1w': end_date - pd.DateOffset(weeks=1),
        '1m': end_date - pd.DateOffset(months=1),
        '3m': end_date - pd.DateOffset(months=3),
        '6m': end_date - pd.DateOffset(months=6),
        '12m': end_date - pd.DateOffset(years=1),
        '2y': end_date - pd.DateOffset(years=2),
        '3y': end_date - pd.DateOffset(years=3),
        '5y': end_date - pd.DateOffset(years=5),
        '10y': end_date - pd.DateOffset(years=10),
        'max': df.index[0]
    }
    
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
        "hist": df_filtered['Hist'].tolist()
    }

@app.get("/manifest.json")
def manifest(): return FileResponse("manifest.json")

@app.get("/sw.js")
def sw(): return FileResponse("sw.js")

@app.get("/", response_class=HTMLResponse)
def index():
    with open("index.html", "r", encoding="utf-8") as f: return f.read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
