# DAZY Infrastructure, Deployment & Disaster Recovery Guide

**Document Version:** 2.0.0  
**Owner:** Tarik (@tarikk786786)  
**System Name:** DAZY Master AI Operating System  
**Classification:** Enterprise Operations Runbook & Recovery Guide

---

## 1. System Requirements & Prerequisites

### Hardware Requirements
- **Host Machine:** Windows 10 / Windows 11 (64-bit) or Linux (Ubuntu 22.04+).
- **CPU:** Quad-Core x86_64 or ARM64 processor (Intel i5/i7, AMD Ryzen 5/7, or Apple Silicon).
- **RAM:** Minimum 8 GB (DAZY idle consumption is strictly < 180 MB; active swarm < 450 MB).
- **Disk Space:** 5 GB free storage for virtual environments, models, and SQLite memory databases.
- **Audio Hardware:** Working microphone input and speaker/headphone output device.

### Software Prerequisites
- **Python:** 3.10 through 3.14 (Python 3.14 verified in production).
- **Node.js:** v18.0.0 or higher (for MCP servers and Biome tooling).
- **Git:** v2.40.0+ with SSH/HTTPS credentials configured.
- **Audio Drivers:** Windows WASAPI or DirectSound audio subsystem.

---

## 2. Local Workstation Bootstrap Runbook

### Step 1: Clone Repository
```powershell
git clone https://github.com/tarikk786786/DAZY-ai-new.git DAZY
cd DAZY
git checkout dazy-transformation
```

### Step 2: Configure Environment & Credentials
Ensure `appinfo11.txt` is present in the root directory and populated with your credentials:
```ini
# Centralized Credential Store (Never commit this file)
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
AIMLAPI_API_KEY=your_aimlapi_key_here
GITHUB_TOKEN=your_github_token_here
ASSISTANT_NAME=DAZY
OWNER_NAME=Tarik
```

### Step 3: Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Verify Audio Peripherals
Execute the audio diagnostic script to ensure microphone and speakers are mapped correctly:
```powershell
python -c "import sounddevice as sd; print(sd.query_devices())"
```

### Step 5: Start DAZY Server Daemon
```powershell
python main.py
```
The server will boot and display:
```
[DAZY Core] Booting DAZY Sovereign AI Operating System...
[DAZY Gateway] Starlette server listening on http://127.0.0.1:8080 (Plain) and 8081 (TLS)
[DAZY Audio] Silero VAD active. Edge TTS voice engine ready: en-IN-NeerjaNeural
[DAZY Memory] SQLite hybrid memory connected at memory/dazy_memory.db
[DAZY Orchestrator] LangGraph real execution engine initialized with SQLite checkpoints.
```

---

## 3. Background Service Management on Windows

To run DAZY continuously in the background on Windows without keeping a command prompt open, configure a Windows Background Task or NSSM service:

### Option A: PowerShell Background Job
```powershell
Start-Process -FilePath "python.exe" -ArgumentList "main.py" -WindowStyle Hidden
```

### Option B: NSSM (Non-Sucking Service Manager)
```powershell
# Install NSSM via Chocolatey or download binary
choco install nssm

# Register DAZY Service
nssm install DAZY-Service "C:\Users\tarik\AppData\Local\Python\pythoncore-3.14-64\python.exe" "C:\Users\tarik\Downloads\FatihMakes\Mark-LVII\main.py"
nssm set DAZY-Service AppDirectory "C:\Users\tarik\Downloads\FatihMakes\Mark-LVII"
nssm set DAZY-Service Start SERVICE_AUTO_START
nssm start DAZY-Service
```

### Process Management & Health Verification
- **Check Process Status:**
  ```powershell
  Get-Process -Name python | Where-Object { $_.CommandLine -like "*main.py*" }
  ```
- **Inspect Port Binding:**
  ```powershell
  netstat -ano | findstr :8080
  ```
- **HTTP Health Probe:**
  ```powershell
  curl http://127.0.0.1:8080/health
  # Response: {"status": "ok", "uptime_seconds": 1420, "active_workers": 0}
  ```

---

## 4. Docker Containerization Specification

For headless deployment or CI/CD pipelines, DAZY provides a containerized configuration:

### `Dockerfile`
```dockerfile
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8080

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    portaudio19-dev \
    libasound2-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080 8081

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://127.0.0.1:8080/health || exit 1

CMD ["python", "main.py"]
```

### `docker-compose.yml`
```yaml
version: '3.8'

services:
  dazy-core:
    build: .
    container_name: dazy_ai_os
    restart: unless-stopped
    ports:
      - "8080:8080"
      - "8081:8081"
    environment:
      - ASSISTANT_NAME=DAZY
      - OWNER_NAME=Tarik
    volumes:
      - ./memory:/app/memory
      - ./config:/app/config
      - ./appinfo11.txt:/app/appinfo11.txt:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://127.0.0.1:8080/health"]
      interval: 15s
      timeout: 5s
      retries: 3
```

---

## 5. Backup & Disaster Recovery Procedures

### SQLite Snapshot Runbook
DAZY databases (`memory/dazy_memory.db`, `memory/langgraph_checkpoints.db`) run in WAL mode. To create a consistent, zero-lock snapshot:

```powershell
# Backup SQLite database using online vacuum snapshot
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
python -c "import sqlite3; con = sqlite3.connect('memory/dazy_memory.db'); con.execute(\"VACUUM INTO 'memory/backups/dazy_memory_$timestamp.db'\"); con.close()"
Write-Host "Backup created: memory/backups/dazy_memory_$timestamp.db"
```

### Database Recovery Runbook
If a database file experiences integrity errors or lock corruption:
1. Stop the DAZY daemon process:
   ```powershell
   Get-Process -Name python | Stop-Process -Force
   ```
2. Move corrupt database files to quarantine:
   ```powershell
   Move-Item memory/dazy_memory.db memory/corrupt_dazy_memory.db.bak
   ```
3. Restore from the latest verified snapshot:
   ```powershell
   Copy-Item (Get-ChildItem memory/backups/*.db | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName memory/dazy_memory.db
   ```
4. Verify database integrity:
   ```powershell
   python -c "import sqlite3; con = sqlite3.connect('memory/dazy_memory.db'); print(con.execute('PRAGMA integrity_check;').fetchall())"
   # Expected Output: [('ok',)]
   ```
5. Restart DAZY daemon.

---

## 6. Incident Response & Auto-Remediation Runbooks

### Runbook 1: Port 8080 Conflict Resolution
If DAZY fails to start due to `[Errno 10048] Address already in use`:
```powershell
$portProcess = (Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue).OwningProcess
if ($portProcess) {
    Write-Warning "Terminating stale process on port 8080: PID $portProcess"
    Stop-Process -Id $portProcess -Force
    Start-Sleep -Seconds 1
}
python main.py
```

### Runbook 2: Cloud Provider Quota Exhaustion (429 Fallback)
If Groq or another provider encounters rate limits during runtime:
1. DAZY automatically shifts traffic through the multi-model fallback ladder (`openai/gpt-oss-120b` -> `qwen/qwen3.8-27b` -> `openai/gpt-oss-20b` -> `DeepSeek` -> `Gemini` -> `AI/ML API`).
2. If all cloud providers are exhausted, DAZY automatically initiates local Ollama fallback on `http://127.0.0.1:11434`.

---

## 7. Zero-Downtime Code Rollback Procedure

If a freshly committed release exhibits regression or fails verification:
```powershell
# Check recent commits
git log --oneline -n 5

# Revert to previous verified commit
git checkout HEAD~1

# Run test suite to verify stability
pytest tests/

# Restart service
Stop-Process -Name python -Force -ErrorAction SilentlyContinue
python main.py
```
