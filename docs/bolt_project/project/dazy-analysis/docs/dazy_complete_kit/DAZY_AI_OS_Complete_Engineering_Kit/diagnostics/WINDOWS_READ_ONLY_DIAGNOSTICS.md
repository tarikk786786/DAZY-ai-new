# Windows Diagnostics — Read-only commands

Run PowerShell as the current user. These commands inspect; they do not delete files or stop services.

## 1. RAM and CPU
```powershell
Get-CimInstance Win32_OperatingSystem |
  Select-Object @{N='TotalRAM_GB';E={[math]::Round($_.TotalVisibleMemorySize/1MB,2)}},
                @{N='FreeRAM_GB';E={[math]::Round($_.FreePhysicalMemory/1MB,2)}}

Get-CimInstance Win32_Processor |
  Select-Object Name, NumberOfCores, NumberOfLogicalProcessors
```

## 2. Top memory processes
```powershell
Get-Process |
  Sort-Object WorkingSet64 -Descending |
  Select-Object -First 30 ProcessName, Id,
    @{N='RAM_MB';E={[math]::Round($_.WorkingSet64/1MB,1)}},
    CPU
```

## 3. Candidate duplicate DAZY processes
```powershell
Get-CimInstance Win32_Process |
  Where-Object { $_.Name -match 'node|python|ollama|dazy|postgres|redis|chrome|msedge' } |
  Select-Object Name, ProcessId, ParentProcessId, ExecutablePath, CommandLine
```
Review command lines carefully; do not terminate based on process name alone.

## 4. Disk free space
```powershell
Get-Volume |
  Select-Object DriveLetter, FileSystemLabel,
    @{N='SizeGB';E={[math]::Round($_.Size/1GB,1)}},
    @{N='FreeGB';E={[math]::Round($_.SizeRemaining/1GB,1)}}
```

## 5. Top-level project folder sizes
Replace path with actual DAZY directory. This is read-only but may take time.
```powershell
$Project = 'C:\PATH\TO\DAZY'
Get-ChildItem -LiteralPath $Project -Force -Directory |
  ForEach-Object {
    $sum = (Get-ChildItem -LiteralPath $_.FullName -File -Recurse -Force -ErrorAction SilentlyContinue |
      Measure-Object -Property Length -Sum).Sum
    [pscustomobject]@{Folder=$_.Name; SizeGB=[math]::Round(($sum/1GB),2)}
  } | Sort-Object SizeGB -Descending
```

## 6. Docker — only if installed
```powershell
docker stats --no-stream
docker system df -v
docker ps -a --size
```
Do not run `docker system prune --volumes` as a diagnostic or automatic fix.

## 7. WSL — only if installed
```powershell
wsl --list --running
```

## 8. GPU
```powershell
Get-CimInstance Win32_VideoController |
  Select-Object Name, DriverVersion, AdapterRAM
```
For NVIDIA only:
```powershell
nvidia-smi
```
Use Task Manager → Performance → GPU for live engine and VRAM readings. Some Windows GPU memory counters are driver dependent.

## 9. Node / package manager
```powershell
node --version
npm --version
Get-ChildItem -Force -Name package-lock.json,pnpm-lock.yaml,yarn.lock,bun.lockb,bun.lock
```
Do not switch package managers before auditing lockfiles and workspace settings.

## 10. Python
```powershell
python --version
python -m pip cache info
```

## 11. Safe evidence bundle
Save outputs to a local text file if useful, but redact usernames, private paths, tokens, API keys and email addresses before sharing. Avoid uploading full process command lines if they contain secrets.
