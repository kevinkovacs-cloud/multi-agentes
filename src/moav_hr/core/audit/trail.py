"""
Audit trail sobre OpenTelemetry (v13 §2.5 / §4.1).

Cada evento registrado emite un span OpenTelemetry (exporter en memoria, aislado por
trace) y se guarda como AuditEvent. Los spans son la telemetría de ejecución que luego
se mapea a un grafo de procedencia RDF (ver core/ontology/abox.py — P1.4).
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from moav_hr.core.audit.events import EventType


def _otel_safe(v: Any):
    if isinstance(v, (str, bool, int, float)):
        return v
    if isinstance(v, (list, tuple)) and all(isinstance(x, (str, int, float, bool)) for x in v):
        return list(v)
    return str(v)


@dataclass
class AuditEvent:
    agent: str
    layer: str
    action: str
    event_type: str = EventType.REGION.value
    region: Optional[int] = None
    detail: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)


class AuditTrail:
    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self.events: list[AuditEvent] = []
        self._exporter = InMemorySpanExporter()
        self._provider = TracerProvider()
        self._provider.add_span_processor(SimpleSpanProcessor(self._exporter))
        self._tracer = self._provider.get_tracer("moav_hr.audit")

    def record(self, agent: str, layer: str, action: str,
               event_type: str = EventType.REGION.value,
               region: Optional[int] = None, **detail) -> AuditEvent:
        ev = AuditEvent(agent, layer, action, event_type, region, detail)
        self.events.append(ev)
        with self._tracer.start_as_current_span(action) as span:
            span.set_attribute("trace_id", self.trace_id)
            span.set_attribute("agent", agent)
            span.set_attribute("layer", layer)
            span.set_attribute("event_type", event_type)
            if region is not None:
                span.set_attribute("region", int(region))
            for k, v in detail.items():
                span.set_attribute(k, _otel_safe(v))
        return ev

    def spans(self):
        """Spans OpenTelemetry finalizados (evidencia de telemetría → RDF)."""
        return self._exporter.get_finished_spans()

    def __len__(self) -> int:
        return len(self.events)
