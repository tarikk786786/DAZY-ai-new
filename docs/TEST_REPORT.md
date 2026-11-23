# DAZY — Test Execution & Verification Report

## 1. Test Environment
* **Platform**: Windows 11 (build 26100)
* **Processor**: 12th Gen Intel(R) Core(TM) i7-12700H (14 cores, 20 logical threads)
* **Graphics**: Intel(R) Iris(R) Xe Graphics (integrated GPU)
* **Memory**: 16 GB RAM
* **Python Runtime**: Python 3.14.4 (Pytest 9.1.1)

---

## 2. Test Execution Summary

| Test Suite | Location | Tests Run | Passed | Failed | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DAZY Unit Suite** | `tests/` | 40 | 40 | 0 | **PASS** |
| **Providers Regression** | `providers/_tests.py` | 99 | 99 | 0 | **PASS** |
| **Total** | | **139** | **139** | **0** | **PASS (100%)** |

---

## 3. Detailed Results

### A. Ambient Intelligence, Memory & Multi-Device (`tests/test_ambient_and_devices.py`)
- `test_resource_governor_evaluation`: Verified CPU, RAM, battery throttle state transitions, bounded task queues, and storage ceiling enforcement. (PASS)
- `test_screen_observer_context_deduplication`: Verified native Win32 foreground window awareness with zero continuous video recording or redundant notifications. (PASS)
- `test_task_observer_and_proactive_alerts`: Verified background task milestone triggers and respectful Hinglish proactive suggestions with cooldown protection. (PASS)
- `test_dazy_3layer_memory`: Verified 3-layer architecture (working memory, event memory with TTL auto-expiration, and long-term memory with SQLite FTS5 full-text keyword ranking). (PASS)
- `test_supabase_sync_offline_resilience`: Verified local-first offline queue and resilience when network or keys are unconfigured. (PASS)
- `test_device_pairing_and_handoff`: Verified one-time 6-digit code generation, QR payloads, mutual verification, nearby discovery radar, and cross-device task context handoff. (PASS)
- `test_coolify_fastapi_backend`: Verified FastAPI backend endpoints (`/health`, `/ready`, `/api/devices/heartbeat`, `/api/devices`, `/api/webhooks/relay`, `/api/events/pull`). (PASS)

### B. Core DAZY Persona, Speech & Providers (`tests/`)
- All 33 previous unit tests for Svara TTS, Higgs TTS, DhVaani, Shrutam2 ASR, SraVaani ASR, Hinglish command token preservation, Emotion lexicon detection, and Activepieces MCP adapter passed. (PASS)

### C. Core Provider Regression Suite (`providers/_tests.py`)
- All 99 core regression tests passed with zero failures.
