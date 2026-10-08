"""Bloque E · E1: el DAG orquestado con LangGraph equivale al orquestador secuencial."""
import pytest

from moav_hr.instances.hr.pipeline import HRPipeline
from moav_hr.instances.hr.synthetic import CANDIDATES


def _eventos(st):
    return [(e.agent, e.layer, e.action, e.event_type, e.region, e.detail)
            for e in st["trail"].events]


def _correr(orquestador, **kw):
    p = HRPipeline(mode="sim", orquestador=orquestador, **kw)
    p.warmup(CANDIDATES)
    return [p.process(c) for c in CANDIDATES]


@pytest.mark.parametrize("kw", [{}, {"topology": "committee", "k": 3}])
def test_langgraph_equivale_al_secuencial_en_el_lote_de_la_poc(kw):
    sec, lg = _correr("secuencial", **kw), _correr("langgraph", **kw)
    assert [s["decision"] for s in sec] == [s["decision"] for s in lg]
    for a, b in zip(sec, lg):
        assert _eventos(a) == _eventos(b)                 # mismos eventos, mismo orden
        assert a["matcher"]["score"] == b["matcher"]["score"]
        assert a["auditor"] == b["auditor"]


def test_el_grafo_es_un_stategraph_de_langgraph():
    from langgraph.graph.state import CompiledStateGraph
    p = HRPipeline(mode="sim", orquestador="langgraph")
    assert isinstance(p.orch.grafo, CompiledStateGraph)
    nodos = list(p.orch.grafo.get_graph().nodes)
    assert nodos[0] == "__start__" and nodos[-1] == "__end__"
    assert "inicio" in nodos and "finalizar" in nodos
    assert "flowchart" in p.orch.mermaid() or "graph" in p.orch.mermaid()


def test_orquestador_invalido():
    with pytest.raises(ValueError):
        HRPipeline(mode="sim", orquestador="otro")


def test_el_default_sigue_siendo_secuencial():
    from moav_hr.core.orchestrator import Orchestrator
    assert isinstance(HRPipeline(mode="sim").orch, Orchestrator)
