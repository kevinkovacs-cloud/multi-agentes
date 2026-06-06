"""
Definición del DAG de agentes sobre LangGraph.

Es la versión "production-stack" del pipeline (el Orchestrator de agents/ es la
versión liviana y portable). Demuestra que el grafo de 5 agentes corre sobre
LangGraph con estado compartido — el stack de orquestación de la propuesta.
"""
from __future__ import annotations

import secrets
from typing import Any, TypedDict

from moav_hr.synthetic import JOB, Candidate
from moav_hr.audit.trail import AuditTrail
from moav_hr.llm import LLMClient
from moav_hr.agents.parser_agent import ParserAgent
from moav_hr.agents.semantic_matcher import SemanticMatcherAgent
from moav_hr.agents.bias_auditor import BiasAuditorAgent
from moav_hr.agents.explainability_agent import ExplainabilityAgent


class PipelineState(TypedDict, total=False):
    candidate: Any
    job: dict
    trace_id: str
    trail: Any
    parser: dict
    matcher: dict
    auditor: dict
    explain: dict
    decision: str


def build_graph(mode: str = "sim", threshold: float = 0.075, llm: LLMClient | None = None):
    """Compila el StateGraph de los 5 agentes."""
    from langgraph.graph import StateGraph, START, END

    llm = llm or LLMClient(mode)
    parser = ParserAgent()
    matcher = SemanticMatcherAgent(llm)
    auditor = BiasAuditorAgent(threshold)
    explainer = ExplainabilityAgent(llm)

    def node(agent):
        def _f(state):
            agent.run(state)
            return state
        return _f

    def orchestrator_node(state):
        a = state["auditor"]
        if a["adjusted_score"] < 0.75:
            decision = "REJECT"
        elif a["blocked"]:
            decision = "ESCALATE_HUMAN"
        else:
            decision = "ADVANCE"
        state["decision"] = decision
        state["trail"].record("Orchestrator", "BIO", "final_decision",
                              decision=decision, score=a["adjusted_score"])
        return state

    g = StateGraph(PipelineState)
    g.add_node("parser", node(parser))
    g.add_node("matcher", node(matcher))
    g.add_node("auditor", node(auditor))
    g.add_node("explainer", node(explainer))
    g.add_node("orchestrator", orchestrator_node)
    g.add_edge(START, "parser")
    g.add_edge("parser", "matcher")
    g.add_edge("matcher", "auditor")
    g.add_edge("auditor", "explainer")
    g.add_edge("explainer", "orchestrator")
    g.add_edge("orchestrator", END)
    return g.compile()


def run_graph(candidate: Candidate, mode: str = "sim", threshold: float = 0.075) -> dict:
    """Conveniencia: corre el grafo LangGraph sobre un candidato."""
    app = build_graph(mode, threshold)
    trace_id = "TRC-" + secrets.token_hex(3).upper()
    state: dict = {
        "candidate": candidate, "job": JOB, "trace_id": trace_id,
        "trail": AuditTrail(trace_id),
    }
    return app.invoke(state)
