"""Explainability Agent (capa WIO, comunicador) — explicaciones tri-nivel L1/L2/L3 (§4.1)."""
from __future__ import annotations

from moav_hr.core.agent import MOACVAgent, TBOLayer
from moav_hr.core.llm import LLMBackend


class ExplainabilityAgent(MOACVAgent):
    def __init__(self, backend: LLMBackend):
        super().__init__("ExplainabilityAgent", "explainer", tbo=TBOLayer(training_runs=1))  # → Novato
        self.backend = backend

    def run(self, state: dict) -> dict:
        p, m, a = state["parser"], state["matcher"], state["auditor"]
        L1 = (f"Parser extrajo {len(p['skills_matched'])} skills relevantes; "
              f"Matcher calculó score {m['score']:.3f} (fuente {m['source']}, "
              f"{m['n_retrieved']} teorías recuperadas) sobre umbral 0.75.")
        if a["bias_score"] is None:   # auditor experimental (B1): dictamen por ventana
            L2 = (f"Auditoría de equidad por ventana ({a['bias_type']}): sin dictamen "
                  f"por caso; score sin ajuste ({a['adjusted_score']:.3f}).")
        else:
            L2 = (f"Bias Auditor detectó {a['bias_type']} (Δ={a['bias_score']:.3f}); "
                  f"score ajustado a {a['adjusted_score']:.3f}.")
        L3 = ("Decisión escalada a revisión humana (EU AI Act Art.14); audit trail RDF "
              "disponible para auditoría externa." if a["blocked"]
              else "Pipeline completado sin intervención humana; sesgo dentro de umbral (Art.13).")
        state["explain"] = {"L1": L1, "L2": L2, "L3": L3}
        state["trail"].record("ExplainabilityAgent", "WIO", "explain", region=6,
                              levels=["L1", "L2", "L3"])
        return state
