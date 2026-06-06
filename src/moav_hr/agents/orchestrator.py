"""
Orchestrator (capa BIO meta) — coordina el DAG de agentes, registra el audit trail
y decide el escalado a revisión humana (EU AI Act Art.14).
"""
from __future__ import annotations

import secrets

from moav_hr.agents.base_agent import MOACVAgent, TBOLayer
from moav_hr.agents.parser_agent import ParserAgent
from moav_hr.agents.semantic_matcher import SemanticMatcherAgent
from moav_hr.agents.bias_auditor import BiasAuditorAgent
from moav_hr.agents.explainability_agent import ExplainabilityAgent
from moav_hr.audit.trail import AuditTrail
from moav_hr.llm import LLMClient, sim_match_score
from moav_hr.synthetic import JOB, Candidate


def _trace_id() -> str:
    return "TRC-" + secrets.token_hex(3).upper()


class Orchestrator(MOACVAgent):
    """Coordina los 5 agentes del pipeline MOACV."""

    def __init__(self, mode: str = "sim", threshold: float = 0.075,
                 llm: LLMClient | None = None):
        super().__init__("Orchestrator", "orchestrator", tbo=TBOLayer(training_runs=4))
        self.llm = llm or LLMClient(mode)
        self.threshold = threshold
        self.parser = ParserAgent()
        self.matcher = SemanticMatcherAgent(self.llm)
        self.auditor = BiasAuditorAgent(threshold)
        self.explainer = ExplainabilityAgent(self.llm)
        self.agents = [self.parser, self.matcher, self.auditor, self.explainer]

    def run_pipeline(self, candidate: Candidate) -> dict:
        """Ejecuta el DAG completo sobre un candidato y devuelve el estado final."""
        trace_id = _trace_id()
        state = {
            "candidate": candidate, "job": JOB, "trace_id": trace_id,
            "trail": AuditTrail(trace_id),
        }
        state["trail"].record("Orchestrator", "BIO", "pipeline_start", candidate=candidate.id)

        for agent in self.agents:
            agent.run(state)

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


def run_baseline(candidate: Candidate) -> dict:
    """
    Caso basal: un único agente (solo matching, sin auditoría de sesgo ni escalado).
    Punto de comparación experimental (caso basal de la propuesta). Determinístico.
    """
    score = sim_match_score(candidate)
    decision = "ADVANCE" if score >= 0.75 else "REJECT"
    return {"candidate": candidate, "score": score, "decision": decision}
