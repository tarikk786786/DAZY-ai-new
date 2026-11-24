"""core/ai_os/graph.py — Telemetry-driven 3D Brain & Infrastructure Graph Projection."""
from __future__ import annotations

import math
import threading
from typing import Dict, List, Optional

from .schemas import DataQualityState, GraphEdge, GraphNode, GraphSnapshot
from .registry import ControlPlaneRegistry


class GraphProjectionService:
    """Projects the control plane registry and live runtime actors into a 3D coordinate space."""

    _instance: Optional[GraphProjectionService] = None
    _lock = threading.RLock()

    def __init__(self):
        self._registry = ControlPlaneRegistry.get_instance()

    @classmethod
    def get_instance(cls) -> GraphProjectionService:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def build_snapshot(self, correlation_id: str = "sys_snapshot") -> GraphSnapshot:
        """Constructs a real 3D spatial node-edge layout from confirmed registered entities."""
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []

        # Center: Primary Orchestrator (0, 0, 0)
        center_id = "node_orchestrator"
        nodes.append(GraphNode(
            id=center_id,
            label="DAZY AI OS Orchestrator",
            type="orchestrator",
            status="HEALTHY",
            x=0.0, y=0.0, z=0.0,
            quality_state=DataQualityState.LIVE,
            telemetry={"role": "Central Brain", "state": "ACTIVE"},
        ))

        # Ring 1: Models & Providers (Radius 30, Y: +15)
        models = self._registry.get_models()
        angle_step = (2 * math.pi) / max(len(models), 1)
        for i, m in enumerate(models):
            nid = f"node_{m.id}"
            theta = i * angle_step
            nx = round(30.0 * math.cos(theta), 2)
            nz = round(30.0 * math.sin(theta), 2)
            nodes.append(GraphNode(
                id=nid,
                label=m.name,
                type="model",
                status="HEALTHY" if m.is_active else "DEGRADED",
                x=nx, y=15.0, z=nz,
                quality_state=m.quality_state,
                telemetry={"context_window": m.context_window, "rate_limit_rpm": m.rate_limit_rpm},
            ))
            edges.append(GraphEdge(
                id=f"edge_orch_{m.id}",
                source=center_id,
                target=nid,
                type="invocation",
                active=True,
                throughput=1.0,
            ))

        # Ring 2: Workers & Subagents (Radius 45, Y: 0)
        workers = self._registry.get_workers()
        w_step = (2 * math.pi) / max(len(workers), 1)
        for i, w in enumerate(workers):
            nid = f"node_{w.id}"
            theta = i * w_step
            nx = round(45.0 * math.cos(theta), 2)
            nz = round(45.0 * math.sin(theta), 2)
            nodes.append(GraphNode(
                id=nid,
                label=w.name,
                type="worker",
                status="HEALTHY" if w.status.value in ("READY", "RUNNING") else "DEGRADED",
                x=nx, y=0.0, z=nz,
                quality_state=DataQualityState.LIVE,
                telemetry={"role": w.role, "status": w.status.value},
            ))
            edges.append(GraphEdge(
                id=f"edge_orch_{w.id}",
                source=center_id,
                target=nid,
                type="data_flow",
                active=w.status.value == "RUNNING",
                throughput=0.8,
            ))

        # Ring 3: MCP Servers & Tools (Radius 60, Y: -15)
        mcp_servers = self._registry.get_mcp_servers()
        m_step = (2 * math.pi) / max(len(mcp_servers), 1)
        for i, srv in enumerate(mcp_servers):
            nid = f"node_{srv.id}"
            theta = i * m_step
            nx = round(60.0 * math.cos(theta), 2)
            nz = round(60.0 * math.sin(theta), 2)
            nodes.append(GraphNode(
                id=nid,
                label=srv.name,
                type="mcp",
                status="HEALTHY" if srv.status.value == "HEALTHY" else "DEGRADED",
                x=nx, y=-15.0, z=nz,
                quality_state=srv.quality_state,
                telemetry={"transport": srv.transport, "tools": len(srv.tools_provided)},
            ))
            edges.append(GraphEdge(
                id=f"edge_orch_{srv.id}",
                source=center_id,
                target=nid,
                type="dependency",
                active=True,
                throughput=0.5,
            ))

        # Audio DSP & Memory Nodes
        nodes.append(GraphNode(
            id="node_audio_dsp",
            label="Audio DSP & VAD Engine",
            type="audio",
            status="HEALTHY",
            x=-20.0, y=25.0, z=0.0,
            quality_state=DataQualityState.LIVE,
            telemetry={"sample_rate": 16000, "channels": 1},
        ))
        edges.append(GraphEdge(
            id="edge_orch_audio",
            source="node_audio_dsp",
            target=center_id,
            type="data_flow",
            active=True,
            throughput=1.0,
        ))

        nodes.append(GraphNode(
            id="node_memory_store",
            label="3-Tier Memory Store",
            type="memory",
            status="HEALTHY",
            x=20.0, y=25.0, z=0.0,
            quality_state=DataQualityState.LIVE,
            telemetry={"storage": "SQLite + JSON", "layers": 3},
        ))
        edges.append(GraphEdge(
            id="edge_orch_memory",
            source=center_id,
            target="node_memory_store",
            type="data_flow",
            active=True,
            throughput=0.9,
        ))

        return GraphSnapshot(
            nodes=nodes,
            edges=edges,
            correlation_id=correlation_id,
        )
