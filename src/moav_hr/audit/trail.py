"""
Audit trail del pipeline.

Colecciona los eventos de cada agente en orden y produce el evento de decisión
JSON-LD. En la tesis este colector se respalda sobre OpenTelemetry + Langfuse;
en la PoC mantenemos un registro en memoria, serializable a JSON-LD.
"""
from __future__ import annotations
import json
import time
from dataclasses import dataclass, field
from typing import Any

from moav_hr.audit.ontology import build_decision_event


@dataclass
class AuditEvent:
    agent: str
    layer: str
    action: str
    detail: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)


class AuditTrail:
    """Registro append-only de eventos de un trace de decisión."""

    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self.events: list[AuditEvent] = []

    def record(self, agent: str, layer: str, action: str, **detail) -> None:
        self.events.append(AuditEvent(agent, layer, action, detail))

    def __len__(self) -> int:
        return len(self.events)

    def decision_event(self, state: dict) -> dict:
        return build_decision_event(state)

    def to_jsonld(self, state: dict, indent: int = 2) -> str:
        return json.dumps(self.decision_event(state), ensure_ascii=False, indent=indent)
