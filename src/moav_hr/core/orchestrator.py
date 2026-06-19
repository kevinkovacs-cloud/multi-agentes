"""
Orquestación del DAG de agentes (v13 Def. 1: M = ⟨G, Θ, Φ, Ω⟩).

Genérico: recibe los agentes ya en orden topológico (Φ), el Monitor Ω y un finalizador
de decisión propio del dominio. Ejecuta el pipeline sobre un estado compartido y registra
el audit trail. NO conoce el dominio (no importa instances/).
"""
from __future__ import annotations
import secrets
from typing import Any, Callable, Optional

from moav_hr.core.agent import MOACVAgent
from moav_hr.core.monitor import FairnessUtilityMonitor
from moav_hr.core.audit.trail import AuditTrail
from moav_hr.core.audit.events import EventType


def new_trace_id() -> str:
    return "TRC-" + secrets.token_hex(3).upper()


class Orchestrator:
    def __init__(self, agents: list[MOACVAgent],
                 monitor: Optional[FairnessUtilityMonitor] = None,
                 finalize: Optional[Callable[[dict], str]] = None):
        self.agents = agents                # orden topológico de G (Φ)
        self.monitor = monitor              # Ω
        self.finalize = finalize            # decisión final del dominio

    def run(self, initial_state: dict[str, Any]) -> dict[str, Any]:
        state = dict(initial_state)
        state.setdefault("trace_id", new_trace_id())
        state.setdefault("trail", AuditTrail(state["trace_id"]))
        if self.monitor is not None:
            state.setdefault("monitor", self.monitor)
        state["trail"].record("Orchestrator", "BIO", "pipeline_start", region=1)

        for agent in self.agents:           # ejecución por orden topológico
            agent.run(state)

        if self.finalize is not None:
            decision = self.finalize(state)
            state["decision"] = decision
            ev = (EventType.ESCALAMIENTO.value if decision == "ESCALATE_HUMAN"
                  else EventType.DECISION.value)
            state["trail"].record("Orchestrator", "BIO", "final_decision",
                                  event_type=ev, region=7, decision=decision)
        return state
