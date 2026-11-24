# Backup the DAZY SQLite database (WAL-aware, safe while running).
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$db = Join-Path $root "backend\data\dazy.db"
if (-not (Test-Path $db)) { Write-Host "No database found at $db"; exit 1 }
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$dest = Join-Path $root "backups"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
$out = Join-Path $dest "dazy-$stamp.db"
# Use sqlite's backup through Python for a consistent copy even while DAZY runs.
& (Join-Path $root ".venv\Scripts\python.exe") -c "import sqlite3; src=sqlite3.connect(r'$db'); dst=sqlite3.connect(r'$out'); src.backup(dst); dst.close(); src.close()"
if ($LASTEXITCODE -eq 0) { Write-Host "Backup written: $out" -ForegroundColor Green } else { Write-Host "Backup failed" -ForegroundColor Red; exit 1 }
