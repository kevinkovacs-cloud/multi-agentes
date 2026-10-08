"""
Orquestación del DAG de agentes con LangGraph (v13 Def. 1: M = ⟨G, Θ, Φ, Ω⟩) — bloque E · E1.

La orquestación con LangGraph existió desde la primera versión (06/06/2026,
`pipeline/dag.py`; rama local `rescate/langgraph-junio`) y quedó fuera del historial al
reorganizarlo. Este módulo la restituye como orquestador del DAG, ahora genérico: no
conoce el dominio (no importa `instances/`).

Diseño. El estado del dominio viaja completo en un único canal (`estado`) del
`StateGraph`: el core no declara las claves del dominio y cada nodo recibe el MISMO
diccionario que recibe el orquestador secuencial (`core/orchestrator.py`). Por eso ambos
orquestadores producen las mismas decisiones y el mismo orden de eventos del audit trail
(lo verifica `tests/test_bloquee_grafo.py`). El grafo es lineal en el orden topológico
dado (Φ): inicio → agentes → finalización. Un comité (`core/committee.py`) es un nodo
más: agrega a sus miembros dentro de su propio `run`.
"""
from __future__ import annotations
from typing import Any, Callable, Optional, TypedDict

from moav_hr.core.audit.events import EventType
from moav_hr.core.audit.trail import AuditTrail
from moav_hr.core.orchestrator import new_trace_id


class CanalEstado(TypedDict):
    """Único canal del StateGraph: el estado del dominio, sin esquema fijo."""
    estado: dict


def _nombres_unicos(agents: list) -> list[str]:
    usados: set[str] = set()
    out = []
    for i, ag in enumerate(agents):
        base = f"{i + 1:02d}_{getattr(ag, 'name', type(ag).__name__)}"
        nombre, j = base, 1
        while nombre in usados:
            j += 1
            nombre = f"{base}_{j}"
        usados.add(nombre)
        out.append(nombre)
    return out


def construir_grafo(agents: list, monitor: Any = None,
                    finalize: Optional[Callable[[dict], str]] = None):
    """Compila el StateGraph lineal inicio → agentes (orden Φ) → finalización."""
    from langgraph.graph import END, START, StateGraph

    def nodo_inicio(canal: CanalEstado) -> CanalEstado:
        state = canal["estado"]
        state.setdefault("trace_id", new_trace_id())
        state.setdefault("trail", AuditTrail(state["trace_id"]))
        if monitor is not None:
            state.setdefault("monitor", monitor)
        state["trail"].record("Orchestrator", "BIO", "pipeline_start", region=1)
        return {"estado": state}

    def nodo_agente(agent):
        def _f(canal: CanalEstado) -> CanalEstado:
            state = canal["estado"]
            agent.run(state)
            return {"estado": state}
        return _f

    def nodo_finalizar(canal: CanalEstado) -> CanalEstado:
        state = canal["estado"]
        decision = finalize(state)
        state["decision"] = decision
        ev = (EventType.ESCALAMIENTO.value if decision == "ESCALATE_HUMAN"
              else EventType.DECISION.value)
        state["trail"].record("Orchestrator", "BIO", "final_decision",
                              event_type=ev, region=7, decision=decision)
        return {"estado": state}

    g = StateGraph(CanalEstado)
    g.add_node("inicio", nodo_inicio)
    previo = "inicio"
    g.add_edge(START, "inicio")
    for nombre, ag in zip(_nombres_unicos(agents), agents):
        g.add_node(nombre, nodo_agente(ag))
        g.add_edge(previo, nombre)
        previo = nombre
    if finalize is not None:
        g.add_node("finalizar", nodo_finalizar)
        g.add_edge(previo, "finalizar")
        previo = "finalizar"
    g.add_edge(previo, END)
    return g.compile()


class OrquestadorLangGraph:
    """Misma interfaz que `core.orchestrator.Orchestrator` (`agents`, `monitor`,
    `finalize`, `run`), con la ejecución delegada en un StateGraph de LangGraph."""

    def __init__(self, agents: list, monitor: Any = None,
                 finalize: Optional[Callable[[dict], str]] = None):
        self.agents = agents
        self.monitor = monitor
        self.finalize = finalize
        self.grafo = construir_grafo(agents, monitor, finalize)

    def run(self, initial_state: dict[str, Any]) -> dict[str, Any]:
        state = dict(initial_state)
        return self.grafo.invoke({"estado": state})["estado"]

    def mermaid(self) -> str:
        """Diagrama del DAG compilado (Mermaid), para la traza y la reunión."""
        return self.grafo.get_graph().draw_mermaid()
