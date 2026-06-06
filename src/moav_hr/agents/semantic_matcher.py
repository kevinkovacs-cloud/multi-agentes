"""Semantic Matcher (capa TBO) — matching semántico candidato↔puesto."""
from __future__ import annotations

from moav_hr.agents.base_agent import MOACVAgent, TBOLayer
from moav_hr.llm import LLMClient


class SemanticMatcherAgent(MOACVAgent):
    def __init__(self, llm: LLMClient):
        super().__init__(
            "SemanticMatcher", "matcher",
            tbo=TBOLayer(training_runs=4),  # → Trained (sin feedback de producción aún)
        )
        self.llm = llm

    def run(self, state: dict) -> dict:
        c = state["candidate"]
        score, source = self.llm.match_score(c)
        state["matcher"] = {"score": score, "source": source}
        state["trail"].record("SemanticMatcher", "TBO", "semantic_matching",
                              score=score, source=source)
        return state
