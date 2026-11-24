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

        self._seed_default_topologies()

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

    def update_worker_status(self, worker_id: str, status: WorkerStatus, error: Optional[str] = None) -> None:
        with self._lock:
            if worker_id in self._workers:
                w = self._workers[worker_id]
                self._workers[worker_id] = w.model_copy(update={
                    "status": status,
                    "error_message": error,
                    "heartbeat_ts": time.time(),
                })

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
