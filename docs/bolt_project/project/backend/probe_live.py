"""
Verifies the local backend can actually reach a real provider when a key exists.
Skipped (honestly) when GEMINI_API_KEY is not configured — never fakes a pass.
Run:  python3 -m backend.probe_live
"""
import json
import os
import sys

from . import config, gateway


def main() -> int:
    db_applied = __import__("backend.db", fromlist=["migrate"]).migrate()
    print(f"[probe] migrations applied: {db_applied or 'none (up to date)'}")
    report = gateway.health(deep=True)
    any_configured = False
    failures = 0
    for p in report["providers"]:
        if p["configured"]:
            any_configured = True
        marker = "OK  " if p["state"] == "healthy" else ("FAIL" if p["state"] == "unhealthy" else "SKIP")
        if p["state"] == "unhealthy":
            failures += 1
        print(f"[probe] {marker} {p['id']:<12} {p['model']:<28} {p['latency_ms']:>5}ms  {p['detail']}")
    if not any_configured:
        print("[probe] No provider keys configured — add backend/.env (see .env.example).")
        return 2
    if any(p["state"] == "healthy" for p in report["providers"]):
        print("[probe] At least one live brain reachable. PASS")
        return 0
    print(f"[probe] All configured providers failed ({failures} unhealthy). Check keys.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
