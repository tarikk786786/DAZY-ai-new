<#
DAZY read-only preflight for Windows.
- Does not stop processes.
- Does not delete files.
- Does not inspect secret values.
- Output is sanitized to basic process/resource metadata.
Usage:
  powershell -ExecutionPolicy Bypass -File .\dazy-preflight.ps1 -ProjectPath "C:\path\to\dazy"
#>
param(
  [Parameter(Mandatory=$false)]
  [string]$ProjectPath = (Get-Location).Path
)

$ErrorActionPreference = "Continue"

Write-Host "`n=== DAZY PREFLIGHT: OS / RAM ===" -ForegroundColor Cyan
Get-CimInstance Win32_OperatingSystem |
  Select-Object Caption, Version,
    @{N='TotalRAM_GB';E={[math]::Round($_.TotalVisibleMemorySize/1MB,2)}},
    @{N='FreeRAM_GB';E={[math]::Round($_.FreePhysicalMemory/1MB,2)}} |
  Format-List

Write-Host "`n=== CPU ===" -ForegroundColor Cyan
Get-CimInstance Win32_Processor |
  Select-Object Name, NumberOfCores, NumberOfLogicalProcessors |
  Format-List

Write-Host "`n=== TOP 25 PROCESSES BY WORKING SET ===" -ForegroundColor Cyan
Get-Process |
  Sort-Object WorkingSet64 -Descending |
  Select-Object -First 25 ProcessName, Id,
    @{N='RAM_MB';E={[math]::Round($_.WorkingSet64/1MB,1)}},
    CPU |
  Format-Table -AutoSize

Write-Host "`n=== RELEVANT PROCESS NAMES (NO COMMAND-LINE SECRETS) ===" -ForegroundColor Cyan
Get-Process |
  Where-Object { $_.ProcessName -match 'node|python|dazy|ollama|chrome|msedge|postgres|redis|docker|wsl' } |
  Select-Object ProcessName, Id,
    @{N='RAM_MB';E={[math]::Round($_.WorkingSet64/1MB,1)}} |
  Sort-Object RAM_MB -Descending |
  Format-Table -AutoSize

Write-Host "`n=== DISKS ===" -ForegroundColor Cyan
Get-Volume |
  Select-Object DriveLetter, FileSystemLabel,
    @{N='SizeGB';E={[math]::Round($_.Size/1GB,1)}},
    @{N='FreeGB';E={[math]::Round($_.SizeRemaining/1GB,1)}} |
  Format-Table -AutoSize

Write-Host "`n=== GPU ===" -ForegroundColor Cyan
Get-CimInstance Win32_VideoController |
  Select-Object Name, DriverVersion, AdapterRAM |
  Format-Table -AutoSize

Write-Host "`n=== PROJECT TOP-LEVEL FOLDERS ===" -ForegroundColor Cyan
if (Test-Path -LiteralPath $ProjectPath) {
  Write-Host "Project: $ProjectPath"
  Get-ChildItem -LiteralPath $ProjectPath -Force -Directory |
    ForEach-Object {
      $sum = (Get-ChildItem -LiteralPath $_.FullName -File -Recurse -Force -ErrorAction SilentlyContinue |
        Measure-Object -Property Length -Sum).Sum
      [pscustomobject]@{ Folder=$_.Name; SizeGB=[math]::Round(($sum/1GB),2) }
    } |
    Sort-Object SizeGB -Descending |
    Format-Table -AutoSize
} else {
  Write-Warning "Project path not found. Re-run with -ProjectPath."
}

Write-Host "`n=== OPTIONAL TOOL AVAILABILITY ===" -ForegroundColor Cyan
$commands = 'node','npm','python','uv','docker','wsl','nvidia-smi','trivy','semgrep','gitleaks','k6','bru'
$availability = foreach ($name in $commands) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  [pscustomobject]@{ Tool=$name; Available=[bool]$cmd; Path=if($cmd){$cmd.Source}else{''} }
}
$availability | Format-Table -AutoSize

Write-Host "`nRead-only preflight complete. Review output before running any cleanup or load test." -ForegroundColor Green
