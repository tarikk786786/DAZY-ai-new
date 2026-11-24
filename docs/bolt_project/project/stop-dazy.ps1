# Gracefully stop the DAZY local backend.
$conn = Get-NetTCPConnection -LocalPort 8787 -ErrorAction SilentlyContinue
if (-not $conn) { Write-Host "DAZY backend is not running."; exit 0 }
$procId = ($conn | Select-Object -First 1).OwningProcess
try { Stop-Process -Id $procId -Force; Write-Host "DAZY backend (pid $procId) stopped." -ForegroundColor Green }
catch { Write-Host "Could not stop pid ${procId}: $_" -ForegroundColor Red; exit 1 }
