$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "ETF dashboard"
Write-Host "Repo: $PWD"
Write-Host ""

$python = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $python = "py"
    $pythonArgs = @("-3")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $python = "python"
    $pythonArgs = @()
} else {
    Write-Host "Python 3 is required. Install from https://www.python.org/downloads/ and tick `"Add python.exe to PATH`"."
    exit 1
}

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[1/3] Creating .venv..."
    & $python @pythonArgs -m venv .venv
} else {
    Write-Host "[1/3] Using existing .venv"
}

Write-Host "[2/3] Installing requirements into .venv..."
& $venvPython -m pip install -r requirements.txt

Write-Host "[3/3] Launching server..."
Write-Host ""
Write-Host "This PC:     http://localhost:8000"
Write-Host "Phone/Wi-Fi: http://THIS-PC-IP:8000"
Write-Host "IPv4 addresses:"
Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notlike "127.*" } |
    ForEach-Object { Write-Host "  $($_.IPAddress)" }
Write-Host ""
Write-Host "Leave this window open. Press Ctrl+C to stop."
Write-Host ""

& $venvPython -m uvicorn app:app --host 0.0.0.0 --port 8000
