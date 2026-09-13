# ETF Technical Analysis Dashboard

Local FastAPI dashboard for ETF price, SMA envelopes, RSI, and MACD. Runs on this PC and is reachable from phones on the same Wi-Fi. No Docker and no Hugging Face. Dependencies stay in `.venv`.

## Setup

1. Install [Python 3](https://www.python.org/downloads/). On Windows, tick **Add python.exe to PATH**.
2. You do not need to create a venv by hand. The run script does that.

## Run

From anywhere, run the script. It `cd`s into this repo, creates `.venv` if needed, installs `requirements.txt` into that venv, then launches the server.

**Command Prompt / double-click**

```bat
c:\repos\personal\etf-dashboard\run.bat
```

**PowerShell**

```powershell
c:\repos\personal\etf-dashboard\run.ps1
```

Then open [http://localhost:8000](http://localhost:8000) in Chrome. Keep the script window open while you use the dashboard. Press Ctrl+C to stop.

`start.bat` is the same as `run.bat`.

### Manual equivalent

```bat
cd /d c:\repos\personal\etf-dashboard
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app:app --host 0.0.0.0 --port 8000
```

## Cast from this PC

1. Turn on **Rotation** if you want ETFs to cycle every 15 seconds.
2. Click **Fullscreen Cast**.
3. In Chrome: menu → **Cast** → pick the TV → **Cast tab**.

## Phone on the same Wi-Fi

The run script prints this PC’s IPv4 addresses. On the phone, open `http://THAT-IP:8000`.

If the phone cannot connect, allow Python on **Private** networks in Windows Firewall for port 8000.

Public internet access is not set up yet.
