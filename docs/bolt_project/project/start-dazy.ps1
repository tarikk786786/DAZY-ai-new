# Start DAZY local backend on 127.0.0.1. Checks the port first.
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$port = 8787
if ($env:DAZY_PORT) { $port = [int]$env:DAZY_PORT }

$conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($conn) {
    Write-Host "Port $port is already in use (probably DAZY is running). Stop it first: .\stop-dazy.ps1" -ForegroundColor Yellow
    exit 1
}

Push-Location $root
Write-Host "Starting DAZY backend on http://127.0.0.1:$port ..." -ForegroundColor Cyan
Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m","backend" -NoNewWindow
Start-Sleep -Seconds 3
try {
    $health = Invoke-RestMethod "http://127.0.0.1:$port/api/v1/system" -TimeoutSec 5
    Write-Host "DAZY is up. Providers configured: $($health.providers_configured -join ', ')" -ForegroundColor Green
    if (-not $health.providers_configured) {
        Write-Host "No AI provider keys set. Add keys to backend\.env, then restart." -ForegroundColor Yellow
    }
} catch {
    Write-Host "Started but health check failed — check backend\data\ logs." -ForegroundColor Red
}
Pop-Location
