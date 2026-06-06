"""Explainability Agent (capa WIO comunicador) — explicaciones tri-nivel L1/L2/L3."""
from __future__ import annotations

from moav_hr.agents.base_agent import MOACVAgent, TBOLayer
from moav_hr.llm import LLMClient


class ExplainabilityAgent(MOACVAgent):
    def __init__(self, llm: LLMClient):
        super().__init__(
            "ExplainabilityAgent", "explainer",
            tbo=TBOLayer(training_runs=1),  # → Novato (recién entrenado)
        )
        self.llm = llm

    def run(self, state: dict) -> dict:
        p, m, a = state["parser"], state["matcher"], state["auditor"]
        L1 = (f"Parser extrajo {len(p['skills_matched'])} skills relevantes "
              f"({', '.join(p['skills_matched']) or 'ninguna'}); "
              f"Matcher calculó score {m['score']:.3f} sobre umbral 0.75.")
        L2 = (f"Bias Auditor detectó {a['bias_type']} (Δ={a['bias_score']:.3f}) en la cadena; "
              f"score ajustado a {a['adjusted_score']:.3f}.")
        L3 = ("Decisión escalada a revisión humana (EU AI Act Art.14); audit trail disponible "
              "para auditoría externa (NYC LL144 + Disp.2/2023)." if a["blocked"]
              else "Pipeline completado sin intervención humana; sesgo dentro de umbral (Art.13).")
        state["explain"] = {
            "L1": self.llm.explain("L1", L1),
            "L2": self.llm.explain("L2", L2),
            "L3": self.llm.explain("L3", L3),
        }
        state["trail"].record("ExplainabilityAgent", "WIO", "explain", levels=["L1", "L2", "L3"])
        return state
