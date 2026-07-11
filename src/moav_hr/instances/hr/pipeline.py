"""
Pipeline de selección de personal (v13 §4.1): cablea los 5 agentes sobre core.Orchestrator
con el Monitor de Utilidad de Equidad. Incluye warmup (siembra de teorías, región 5),
caso basal y helpers de métricas.
"""
from __future__ import annotations

from moav_hr.core.llm import LLMBackend
from moav_hr.core.monitor import FairnessUtilityMonitor
from moav_hr.core.orchestrator import Orchestrator
from moav_hr.instances.hr.parser_agent import ParserAgent, normalize_profile, build_si
from moav_hr.instances.hr.semantic_matcher import SemanticMatcherAgent
from moav_hr.instances.hr.bias_auditor import BiasAuditorAgent
from moav_hr.instances.hr.explainability_agent import ExplainabilityAgent
from moav_hr.instances.hr.scoring import sim_match_score
from moav_hr.instances.hr.synthetic import Candidate, JOB


def _finalize(state: dict) -> str:
    a = state["auditor"]
    if a["adjusted_score"] < 0.75:
        return "REJECT"
    return "ESCALATE_HUMAN" if a["blocked"] else "ADVANCE"


class HRPipeline:
    def __init__(self, mode: str = "sim", criterion: str = "demographic_parity",
                 attr: str = "origin_group", threshold: float = 0.075,
                 heterogeneous_reputation: bool = False):
        # N3: reputación heterogénea para nodos transformadores (Parser ← 1−d̂_TV).
        # Default OFF: decisión pendiente con la dirección; los decisores siempre
        # acumulan fair(W) sobre SUS PROPIAS salidas (ver run_poc).
        self.heterogeneous_reputation = heterogeneous_reputation
        self.backend = LLMBackend(mode)
        self.parser = ParserAgent()
        self.matcher = SemanticMatcherAgent(self.backend)
        self.auditor = BiasAuditorAgent(threshold)
        self.explainer = ExplainabilityAgent(self.backend)
        self.monitor = FairnessUtilityMonitor(criterion=criterion, attr=attr,
                                              disparity_threshold=threshold)
        self.orch = Orchestrator([self.parser, self.matcher, self.auditor, self.explainer],
                                 monitor=self.monitor, finalize=_finalize)

    @property
    def agents(self):
        return self.orch.agents

    def warmup(self, candidates) -> int:
        """Siembra la base de teorías del matcher con experiencia (Si → acción correcta)."""
        for c in candidates:
            si = build_si(normalize_profile(c))
            action = "ADVANCE" if c.true_qual >= 0.75 else "REJECT"
            self.matcher.learn(si, action, {"outcome": action}, success=True, u=0.9)
        return len(self.matcher.theories)

    def process(self, candidate: Candidate) -> dict:
        return self.orch.run({"candidate": candidate, "job": JOB})


def run_baseline(candidate: Candidate) -> dict:
    """Caso basal (§4.2): un único agente, sin auditoría ni ciclo de vida."""
    score = sim_match_score(candidate)
    return {"candidate": candidate, "score": score,
            "decision": "ADVANCE" if score >= 0.75 else "REJECT"}


def record_of(state: dict) -> dict:
    """Record para métricas de fairness desde un estado procesado.

    Incluye matcher_score (N3): permite computar la equidad ATRIBUIBLE al matcher
    (decisión que sus scores implican por umbral), separada de la del pipeline final.
    """
    c = state["candidate"]
    a = state["auditor"]
    return {"gender": c.gender, "origin_group": c.origin_group, "decision": state["decision"],
            "true_qual": c.true_qual, "score": a["adjusted_score"], "bias_risk": c.bias_risk,
            "matcher_score": state["matcher"]["score"]}


def matcher_view(records: list[dict], threshold: float = 0.75) -> list[dict]:
    """Vista de la ventana ATRIBUIDA al matcher (N3): la decisión de cada record se
    reemplaza por la que implican sus propios scores (umbral), sin auditor ni humano."""
    return [dict(r, decision=("ADVANCE" if r["matcher_score"] >= threshold else "REJECT"))
            for r in records]
