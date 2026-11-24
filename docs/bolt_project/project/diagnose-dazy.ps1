# Diagnose DAZY: runtime, database, provider reachability. Read-only.
$ErrorActionPreference = "Continue"
$root = $PSScriptRoot
Write-Host "=== DAZY diagnostics ===" -ForegroundColor Cyan

$py = Join-Path $root ".venv\Scripts\python.exe"
Write-Host "[1/3] Runtime:" -NoNewline
if (Test-Path $py) { Write-Host " venv OK" -ForegroundColor Green } else { Write-Host " venv MISSING — run install.ps1" -ForegroundColor Red }

Write-Host "[2/3] Database:"
& $py -c "from backend import config; print('  path:', config.DB_PATH); print('  exists:', config.DB_PATH.exists())"

Write-Host "[3/3] Providers (live probe):"
& $py -m backend.probe_live
Write-Host "Diagnostics complete."
