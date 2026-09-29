# run.ps1 - start the face verification API.
# Local only (default):    powershell -ExecutionPolicy Bypass -File .\run.ps1
# Reachable from network:  powershell -ExecutionPolicy Bypass -File .\run.ps1 -HostAddress 0.0.0.0
param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8000
)

Set-Location $PSScriptRoot

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "No venv found. Run setup.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "Starting on port $Port. Docs: http://localhost:$Port/docs"
Write-Host "The first start downloads and loads the models, which can take a few minutes."
& .\venv\Scripts\python.exe -m uvicorn app.main:app --host $HostAddress --port $Port
