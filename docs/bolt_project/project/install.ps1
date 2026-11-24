# DAZY AI OS — Windows installer. Run: powershell -ExecutionPolicy Bypass -File install.ps1
$ErrorActionPreference = "Stop"
Write-Host "=== DAZY AI OS installer ===" -ForegroundColor Cyan

# 1. Python check
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { Write-Host "Python not found. Install Python 3.11+ from python.org, then re-run." -ForegroundColor Red; exit 1 }
$ver = (& python --version) 2>&1
Write-Host "Found $ver"

# 2. Virtual environment
$root = $PSScriptRoot
Push-Location $root
python -m venv .venv
if ($LASTEXITCODE -ne 0) { Write-Host "venv creation failed" -ForegroundColor Red; exit 1 }

# 3. Dependencies
$pip = ".\.venv\Scripts\pip.exe"
& $pip install --quiet fastapi "uvicorn[standard]" httpx pydantic pytest
if ($LASTEXITCODE -ne 0) { Write-Host "dependency install failed" -ForegroundColor Red; exit 1 }

# 4. Local database + config template
if (-not (Test-Path "backend\.env")) {
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host "Created backend\.env — add your API keys there (GEMINI_API_KEY at minimum)." -ForegroundColor Yellow
}
& python -c "from backend import db; applied = db.migrate(); print('migrations applied:', applied or 'none (up to date)')"
if ($LASTEXITCODE -ne 0) { Write-Host "database init failed" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "Install complete. Start DAZY with:  .\start-dazy.ps1" -ForegroundColor Green
Pop-Location
