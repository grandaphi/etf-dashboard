@echo off
setlocal
cd /d "%~dp0"

echo.
echo ETF dashboard
echo Repo: %CD%
echo.

where py >nul 2>&1
if %ERRORLEVEL%==0 (
    set "PY=py -3"
) else (
    set "PY=python"
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creating .venv...
    %PY% -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo Python 3 is required. Install from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
        pause
        exit /b 1
    )
) else (
    echo [1/3] Using existing .venv
)

echo [2/3] Installing requirements into .venv...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo Failed to install dependencies into .venv.
    pause
    exit /b 1
)

echo [3/3] Launching server...
echo.
echo This PC:     http://localhost:8000
echo Phone/Wi-Fi: http://THIS-PC-IP:8000
echo IPv4 addresses:
ipconfig | findstr /i "IPv4"
echo.
echo Leave this window open. Press Ctrl+C to stop.
echo.

".venv\Scripts\python.exe" -m uvicorn app:app --host 0.0.0.0 --port 8000
