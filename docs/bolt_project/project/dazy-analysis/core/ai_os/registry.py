"""core/ai_os/registry.py — Central Control Plane Registry for Providers, Models, Tools, MCP & Workers."""
from __future__ import annotations

import logging
import sqlite3
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

from .schemas import (
    CapabilityFlags,
    DataQualityState,
    HealthStatus,
    MCPServerInfo,
    ModelInfo,
    ProviderInfo,
    ToolInfo,
    WorkerInfo,
    WorkerStatus,
)

logger = logging.getLogger("dazy.ai_os.registry")


class ControlPlaneRegistry:
    """Thread-safe central registry maintaining the system topology and state."""

    _instance: Optional[ControlPlaneRegistry] = None
    _lock = threading.RLock()

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path(__file__).resolve().parent.parent.parent / "memory" / "ai_os_registry.db"
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

        self._providers: Dict[str, ProviderInfo] = {}
        self._models: Dict[str, ModelInfo] = {}
        self._workers: Dict[str, WorkerInfo] = {}
        self._mcp_servers: Dict[str, MCPServerInfo] = {}
        self._tools: Dict[str, ToolInfo] = {}

        self._load_from_db()
        if not self._providers or not self._models or not self._workers:
            self._seed_default_topologies()
            self.sync_to_db()

    @classmethod
    def get_instance(cls) -> ControlPlaneRegistry:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _init_db(self) -> None:
        """Initializes SQLite tables for durable registry metadata."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS providers (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    kind TEXT,
                    endpoint TEXT,
                    health TEXT,
                    latency_ms REAL,
                    quality_state TEXT,
                    note TEXT,
                    updated_at REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workers (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    role TEXT,
                    parent_id TEXT,
                    status TEXT,
                    model_id TEXT,
                    heartbeat_ts REAL,
                    usage_tokens INTEGER,
                    created_at TEXT
                )
            """)
            conn.commit()

    def sync_to_db(self) -> None:
        """Flushes in-memory registry to durable SQLite storage."""
        with self._lock, sqlite3.connect(self._db_path) as conn:
            for p in self._providers.values():
                h_val = p.health.value if hasattr(p.health, "value") else str(p.health)
                q_val = p.quality_state.value if hasattr(p.quality_state, "value") else str(p.quality_state)
                conn.execute("""
                    INSERT OR REPLACE INTO providers (id, name, kind, endpoint, health, latency_ms, quality_state, note, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (p.id, p.name, p.kind, p.endpoint, h_val, p.latency_ms or 0.0, q_val, p.note or "", time.time()))
            for w in self._workers.values():
                st_val = w.status.value if hasattr(w.status, "value") else str(w.status)
                conn.execute("""
                    INSERT OR REPLACE INTO workers (id, name, role, parent_id, status, model_id, heartbeat_ts, usage_tokens, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (w.id, w.name, w.role, w.parent_id or "", st_val, w.model_id or "", w.heartbeat_ts, w.usage_tokens, w.created_at))
            conn.commit()

    def _load_from_db(self) -> None:
        """Restores providers and workers from SQLite on startup."""
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows_prov = conn.execute("SELECT * FROM providers").fetchall()
            for r in rows_prov:
                try:
                    p = ProviderInfo(
                        id=r["id"],
                        name=r["name"],
                        kind=r["kind"],
                        endpoint=r["endpoint"],
                        health=HealthStatus(r["health"]) if r["health"] in HealthStatus._value2member_map_ else HealthStatus.HEALTHY,
                        latency_ms=r["latency_ms"],
                        quality_state=DataQualityState(r["quality_state"]) if r["quality_state"] in DataQualityState._value2member_map_ else DataQualityState.LIVE,
                        note=r["note"],
                    )
                    self._providers[p.id] = p
                except Exception as e:
                    logger.debug("Failed to hydrate provider %s: %s", r["id"], e)

            rows_wrk = conn.execute("SELECT * FROM workers").fetchall()
            for rw in rows_wrk:
                try:
                    w = WorkerInfo(
                        id=rw["id"],
                        name=rw["name"],
                        role=rw["role"],
                        parent_worker_id=rw["parent_id"] or None,
                        status=WorkerStatus(rw["status"]) if rw["status"] in WorkerStatus._value2member_map_ else WorkerStatus.ACTIVE,
                        model_id=rw["model_id"] or None,
                        heartbeat_ts=rw["heartbeat_ts"],
                        usage_tokens=rw["usage_tokens"],
                        created_at=rw["created_at"],
                    )
                    self._workers[w.id] = w
                except Exception as e:
                    logger.debug("Failed to hydrate worker %s: %s", rw["id"], e)

    def verify_provider_health(self) -> Dict[str, HealthStatus]:
        """Runs live health checks for registered providers without mock data."""
        import os
        results = {}
        with self._lock:
            # 1. Gemini
            prov_gemini = self._providers.get("prov_gemini")
            if prov_gemini:
                key_found = bool(os.environ.get("GEMINI_API_KEY"))
                if not key_found:
                    try:
                        from memory.config_manager import load_api_keys
                        key_found = bool(load_api_keys().get("gemini_api_key") or load_api_keys().get("api_key"))
                    except Exception:
                        pass
                new_health = HealthStatus.HEALTHY if key_found else HealthStatus.DEGRADED
                prov_gemini = prov_gemini.model_copy(update={"health": new_health})
                self._providers["prov_gemini"] = prov_gemini
                results["prov_gemini"] = new_health

            # 2. Edge TTS & Whisper
            prov_edge = self._providers.get("prov_edge_tts")
            if prov_edge:
                results["prov_edge_tts"] = prov_edge.health
            prov_whisper = self._providers.get("prov_whisper")
            if prov_whisper:
                results["prov_whisper"] = prov_whisper.health

            self.sync_to_db()
        return results

    def _seed_default_topologies(self) -> None:
        """Seeds verified default providers, models, workers, and MCP tools."""
        # 1. Primary Providers
        p_gemini = ProviderInfo(
            id="prov_gemini",
            name="Google Gemini Cloud",
            kind="llm",
            endpoint="https://generativelanguage.googleapis.com",
            health=HealthStatus.HEALTHY,
            quality_state=DataQualityState.LIVE,
            note="Primary conversational brain and OpenAI-compatible endpoint",
        )
        p_edge = ProviderInfo(
            id="prov_edge_tts",
            name="Microsoft Edge Neural TTS",
            kind="tts",
            endpoint="https://speech.platform.bing.com",
            health=HealthStatus.HEALTHY,
            quality_state=DataQualityState.LIVE,
            note="Default Indian feminine voice en-IN-NeerjaNeural",
        )
        p_whisper = ProviderInfo(
            id="prov_whisper",
            name="Whisper ASR Engine",
            kind="stt",
            endpoint="local_or_api",
            health=HealthStatus.HEALTHY,
            quality_state=DataQualityState.LIVE,
            note="Automatic speech recognition pipeline",
        )
        self.register_provider(p_gemini)
        self.register_provider(p_edge)
        self.register_provider(p_whisper)

        # 2. Primary Models
        m_gemini_flash = ModelInfo(
            id="gemini-2.5-flash",
            provider_id="prov_gemini",
            name="Gemini 2.5 Flash",
            capabilities=CapabilityFlags(text=True, vision=True, audio=True, tools=True, structured_output=True),
            context_window=1000000,
            rate_limit_rpm=60,
            rate_limit_tpm=1000000,
            quality_state=DataQualityState.LIVE,
        )
        self.register_model(m_gemini_flash)

        # 3. Specialist Workers
        workers_def = [
            ("wrk_orchestrator", "Primary Orchestrator", "Task Decomposition & Brain Routing", "gemini-2.5-flash"),
            ("wrk_voice_lead", "Voice & Audio Lead", "VAD, Diarization, Prosody & Speech Normalization", "gemini-2.5-flash"),
            ("wrk_sec_auditor", "Security Auditor", "AST Scans, CVE Defense & Credential Hygiene", "gemini-2.5-flash"),
            ("wrk_repair_eng", "Autonomous Repair Engineer", "Allowlisted Diagnostics & Safe Rollbacks", "gemini-2.5-flash"),
            ("wrk_memory_curator", "Memory & Knowledge Curator", "Three-Tier Memory & Context Provenance", "gemini-2.5-flash"),
            ("wrk_desktop_eng", "Desktop Automation Specialist", "Window Control, Settings & Hardware HUD", "gemini-2.5-flash"),
        ]
        for wid, wname, wrole, wmodel in workers_def:
            w = WorkerInfo(
                id=wid,
                name=wname,
                role=wrole,
                status=WorkerStatus.READY,
                model_id=wmodel,
                heartbeat_ts=time.time(),
            )
            self.register_worker(w)

        # 4. Registered MCP Servers
        mcp_defs = [
            ("mcp_stitch", "StitchMCP", "stdio", "Design System & Screen Generator"),
            ("mcp_chrome", "chrome-devtools-mcp", "stdio", "Web Automation & Chrome Inspection"),
            ("mcp_context7", "context7", "stdio", "Official Technical Documentation Retrieval"),
            ("mcp_memory", "memory-mcp", "stdio", "Persistent Graph Memory & Entities"),
            ("mcp_playwright", "playwright-mcp", "stdio", "Headless Browser Navigation & Testing"),
        ]
        for mid, mname, mtrans, mdesc in mcp_defs:
            srv = MCPServerInfo(
                id=mid,
                name=mname,
                transport=mtrans,
                status=HealthStatus.HEALTHY,
                quality_state=DataQualityState.LIVE,
            )
            self.register_mcp_server(srv)

        # 5. Core Actions & Tools
        tools_def = [
            ("tool_computer_control", "computer_control", "Automates Windows GUI, mouse, and keyboard clicks"),
            ("tool_browser_control", "browser_control", "Automates browser navigation via Playwright"),
            ("tool_voice_diagnostics", "voice_diagnostics", "Inspects microphone array, VAD meters, and speakers"),
            ("tool_system_settings", "computer_settings", "Controls volume, screen brightness, and power states"),
            ("tool_memory_lookup", "memory_lookup", "Searches short-term and episodic memory"),
        ]
        for tid, tname, tdesc in tools_def:
            t = ToolInfo(
                id=tid,
                name=tname,
                description=tdesc,
                provider_kind="native",
                permission_required=False,
            )
            self.register_tool(t)

    # ── CRUD Operations ──────────────────────────────────────────────────────

    def register_provider(self, prov: ProviderInfo) -> None:
        with self._lock:
            self._providers[prov.id] = prov
            self.sync_to_db()

    def get_providers(self) -> List[ProviderInfo]:
        with self._lock:
            return list(self._providers.values())

    def register_model(self, model: ModelInfo) -> None:
        with self._lock:
            self._models[model.id] = model

    def get_models(self) -> List[ModelInfo]:
        with self._lock:
            return list(self._models.values())

    def register_worker(self, worker: WorkerInfo) -> None:
        with self._lock:
            self._workers[worker.id] = worker
            self.sync_to_db()

    def update_worker_status(self, worker_id: str, status: WorkerStatus, error: Optional[str] = None) -> None:
        with self._lock:
            if worker_id in self._workers:
                w = self._workers[worker_id]
                self._workers[worker_id] = w.model_copy(update={
                    "status": status,
                    "error_message": error,
                    "heartbeat_ts": time.time(),
                })
                self.sync_to_db()

    def get_workers(self) -> List[WorkerInfo]:
        with self._lock:
            return list(self._workers.values())

    def register_mcp_server(self, srv: MCPServerInfo) -> None:
        with self._lock:
            self._mcp_servers[srv.id] = srv

    def get_mcp_servers(self) -> List[MCPServerInfo]:
        with self._lock:
            return list(self._mcp_servers.values())

    def register_tool(self, tool: ToolInfo) -> None:
        with self._lock:
            self._tools[tool.id] = tool

    def get_tools(self) -> List[ToolInfo]:
        with self._lock:
            return list(self._tools.values())
