"""core/ai_os/telemetry.py — Distributed Tracing, Metrics, and Structured Telemetry.

Provides:
- Span and trace tracking with correlation IDs.
- Latency, token usage, and system metric accumulation.
- Thread-safe in-memory ring buffer of recent spans and log events.
- Real-time event broadcasting hook.
"""

from __future__ import annotations

import collections
import contextlib
import dataclasses
import datetime
import logging
import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("dazy.ai_os.telemetry")


@dataclasses.dataclass
class TraceSpan:
    trace_id: str
    span_id: str
    name: str
    parent_span_id: Optional[str] = None
    start_time_ns: int = dataclasses.field(default_factory=time.time_ns)
    end_time_ns: Optional[int] = None
    duration_ms: float = 0.0
    status: str = "RUNNING"  # RUNNING, OK, ERROR
    attributes: Dict[str, Any] = dataclasses.field(default_factory=dict)
    events: List[Dict[str, Any]] = dataclasses.field(default_factory=list)

    def finish(self, status: str = "OK", error: Optional[Exception] = None) -> None:
        self.end_time_ns = time.time_ns()
        self.duration_ms = round((self.end_time_ns - self.start_time_ns) / 1_000_000.0, 3)
        self.status = status
        if error:
            self.attributes["error.type"] = type(error).__name__
            self.attributes["error.message"] = str(error)
            self.status = "ERROR"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "start_time_iso": datetime.datetime.fromtimestamp(
                self.start_time_ns / 1e9, tz=datetime.timezone.utc
            ).isoformat(),
            "duration_ms": self.duration_ms,
            "status": self.status,
            "attributes": self.attributes,
            "events": self.events,
        }


class TelemetryService:
    """Thread-safe telemetry collector, tracing hub, and metrics aggregator."""

    _instance: Optional[TelemetryService] = None
    _lock = threading.Lock()

    def __init__(self, max_spans: int = 2000, max_logs: int = 1000):
        self._max_spans = max_spans
        self._spans: collections.deque[TraceSpan] = collections.deque(maxlen=max_spans)
        self._logs: collections.deque[Dict[str, Any]] = collections.deque(maxlen=max_logs)
        self._active_spans: Dict[str, TraceSpan] = {}
        self._metrics_lock = threading.Lock()
        self._metrics: Dict[str, float] = {
            "requests_total": 0.0,
            "requests_failed": 0.0,
            "tokens_prompt_total": 0.0,
            "tokens_completion_total": 0.0,
            "tokens_total": 0.0,
            "avg_latency_ms": 0.0,
            "total_latency_ms": 0.0,
            "audio_buffer_underruns": 0.0,
            "active_turns": 0.0,
        }
        self._subscribers: List[Callable[[Dict[str, Any]], None]] = []

    @classmethod
    def get_instance(cls) -> TelemetryService:
        with cls._lock:
            if cls._instance is None:
                cls._instance = TelemetryService()
            return cls._instance

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        with self._metrics_lock:
            if callback not in self._subscribers:
                self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        with self._metrics_lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

    def _notify(self, event: Dict[str, Any]) -> None:
        subscribers_snapshot = list(self._subscribers)
        for sub in subscribers_snapshot:
            try:
                sub(event)
            except Exception as e:
                logger.debug("Telemetry subscriber error: %s", e)

    @contextlib.contextmanager
    def start_span(
        self,
        name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        t_id = trace_id or f"trc_{uuid.uuid4().hex[:12]}"
        s_id = f"spn_{uuid.uuid4().hex[:8]}"
        span = TraceSpan(
            trace_id=t_id,
            span_id=s_id,
            parent_span_id=parent_span_id,
            name=name,
            attributes=attributes or {},
        )
        with self._metrics_lock:
            self._active_spans[s_id] = span

        err: Optional[Exception] = None
        try:
            yield span
        except Exception as exc:
            err = exc
            raise
        finally:
            status = "ERROR" if err else "OK"
            span.finish(status=status, error=err)
            with self._metrics_lock:
                self._active_spans.pop(s_id, None)
                self._spans.append(span)
                # Update metrics
                self._metrics["requests_total"] += 1.0
                if err:
                    self._metrics["requests_failed"] += 1.0
                self._metrics["total_latency_ms"] += span.duration_ms
                if self._metrics["requests_total"] > 0:
                    self._metrics["avg_latency_ms"] = round(
                        self._metrics["total_latency_ms"] / self._metrics["requests_total"], 2
                    )

            self._notify({
                "type": "trace_span",
                "span": span.to_dict(),
            })

    def record_tokens(self, prompt_tokens: int, completion_tokens: int) -> None:
        with self._metrics_lock:
            self._metrics["tokens_prompt_total"] += prompt_tokens
            self._metrics["tokens_completion_total"] += completion_tokens
            self._metrics["tokens_total"] += (prompt_tokens + completion_tokens)
        self._notify({
            "type": "metric_update",
            "metric": "tokens",
            "values": {
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": self._metrics["tokens_total"],
            },
        })

    def record_counter(self, name: str, value: float = 1.0) -> None:
        with self._metrics_lock:
            self._metrics[name] = self._metrics.get(name, 0.0) + value

    def set_gauge(self, name: str, value: float) -> None:
        with self._metrics_lock:
            self._metrics[name] = value

    def log_event(self, level: str, message: str, correlation_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> None:
        entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": level.upper(),
            "message": message,
            "correlation_id": correlation_id or "",
            "data": data or {},
        }
        with self._metrics_lock:
            self._logs.append(entry)
        self._notify({
            "type": "telemetry_log",
            "log": entry,
        })

    def get_summary(self) -> Dict[str, Any]:
        with self._metrics_lock:
            metrics_copy = dict(self._metrics)
            recent_spans = [s.to_dict() for s in list(self._spans)[-50:]]
            recent_logs = list(self._logs)[-50:]
            active_count = len(self._active_spans)

        return {
            "metrics": metrics_copy,
            "active_spans_count": active_count,
            "recent_spans": recent_spans,
            "recent_logs": recent_logs,
        }
