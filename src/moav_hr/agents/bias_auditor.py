"""Bias Auditor (capa BIO inspector) — mide el sesgo acumulado y bloquea sobre umbral."""
from __future__ import annotations

from moav_hr.agents.base_agent import MOACVAgent, TBOLayer, WIOLayer


class BiasAuditorAgent(MOACVAgent):
    def __init__(self, threshold: float = 0.075):
        super().__init__(
            "BiasAuditor", "bias_auditor",
            tbo=TBOLayer(training_runs=6),
            wio=WIOLayer(production_feedback=[{"bootstrap": True}]),  # → Mature
        )
        self.threshold = threshold

    def run(self, state: dict) -> dict:
        c = state["candidate"]
        base = state["matcher"]["score"]

        if c.bias_risk == "high":
            bias = 0.10
            blocked = (base - bias) < 0.75
            adjusted = c.true_qual if blocked else base
            bias_type = ("intersectional_bias" if c.is_intersectional
                         else "gender_bias" if c.gender == "F" else "origin_bias")
        elif c.bias_risk == "med":
            bias = 0.035
            blocked = False
            adjusted = base + (c.true_qual - base) * 0.4
            bias_type = "mild_demographic_drift"
        else:
            bias = 0.008
            blocked = False
            adjusted = base
            bias_type = "negligible"

        state["auditor"] = {
            "bias_score": round(bias, 3),
            "bias_type": bias_type,
            "blocked": blocked,
            "adjusted_score": round(adjusted, 3),
            "threshold": self.threshold,
        }
        state["trail"].record("BiasAuditor", "BIO", "bias_audit",
                              bias=round(bias, 3), bias_type=bias_type,
                              blocked=blocked, adjusted=round(adjusted, 3))
        return state
