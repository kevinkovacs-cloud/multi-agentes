"""
Auditor EXPERIMENTAL sin oráculo (B1) — el Ω que usan los experimentos de los Ejes 1–2.

Modelo de acceso DECLARADO (como un auditor de NYC LL144): ve las decisiones/scores
observados del lote y los atributos protegidos SOLO para agregación por ventana. Tiene
PROHIBIDO por construcción leer variables del generador (`bias_risk`, `true_qual`):
su `run` recibe una vista filtrada del estado (observable_view) y un test lo verifica
con un candidato-centinela que registra accesos.

Diferencias con el auditor demostrativo (bias_auditor.py):
  · no asigna sesgo por etiqueta — la disparidad se ESTIMA de las decisiones;
  · no ajusta scores NUNCA;
  · no decide por caso: acumula la ventana y al cierre pide la auditoría CERTIFICADA
    (LCB > τ_b ⇒ FPR ≤ δ bajo H₀, core/stats.py).

Alcance: criterio demographic_parity (observable en runtime). Equalized odds requiere
la etiqueta y* — es métrica de EVALUACIÓN con ground-truth, no de auditoría en línea.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from moav_hr.core.agent import MOACVAgent, TBOLayer
from moav_hr.core import fairness, stats

# claves del generador que el auditor experimental NO puede ver
_FORBIDDEN_ATTRS = ("bias_risk", "true_qual", "match_score")


def observable_view(state: dict) -> dict:
    """
    Vista OBSERVABLE del estado para el auditor experimental: score del matcher, Si
    normalizada y atributos protegidos (para agregación por ventana). Excluye por
    construcción toda variable del generador (bias_risk, true_qual, match_score).
    """
    c = state["candidate"]
    return {
        "score": state["matcher"]["score"],
        "si": state["parser"]["si"],
        "origin_group": c.origin_group,
        "gender": c.gender,
    }


@dataclass
class ExpWindowAudit:
    n: int
    disparity: float           # |Δ̂| puntual (DP sobre decisiones observadas)
    lcb: float                 # cota inferior de confianza de |Δ| (Hoeffding, δ)
    blocked: bool              # lcb > τ_b (certificado)
    delta: float
    attr: str


class ExperimentalBiasAuditor(MOACVAgent):
    """Ω experimental: acumula ventana, certifica al cierre, jamás ajusta scores."""

    def __init__(self, threshold: float = 0.075, attr: str = "origin_group",
                 decision_threshold: float = 0.75):
        super().__init__("BiasAuditorExp", "bias_auditor", tbo=TBOLayer(training_runs=6))
        self.threshold = threshold
        self.attr = attr
        self.decision_threshold = decision_threshold
        self._window: list[dict] = []

    def run(self, state: dict) -> dict:
        view = observable_view(state)                     # única entrada permitida
        decision = "ADVANCE" if view["score"] >= self.decision_threshold else "REJECT"
        self._window.append({self.attr: view[self.attr], "decision": decision})
        state["auditor"] = {
            "bias_score": None,                # no hay proxy por etiqueta: se estima por ventana
            "bias_type": "exp(por-ventana)",
            "blocked": False,                  # el bloqueo es de VENTANA, no por caso
            "adjusted_score": view["score"],   # NUNCA ajusta el score
            "threshold": self.threshold,
        }
        state["trail"].record("BiasAuditorExp", "BIO", "bias_audit_exp", region=4,
                              window_n=len(self._window))
        return state

    def close_window(self, delta: float = 0.05) -> Optional[ExpWindowAudit]:
        """Cierra la ventana acumulada: |Δ̂| puntual + LCB certificada (2 grupos)."""
        if not self._window:
            return None
        groups: dict[str, list[str]] = {}
        for r in self._window:
            groups.setdefault(str(r[self.attr]), []).append(r["decision"])
        if len(groups) != 2:
            raise ValueError("la auditoría certificada requiere exactamente 2 grupos")
        (da, db) = groups.values()
        pos_a = sum(1 for d in da if d in fairness.POSITIVE)
        pos_b = sum(1 for d in db if d in fairness.POSITIVE)
        d_hat = abs(pos_a / len(da) - pos_b / len(db))
        lcb = stats.lcb_abs_diff_rates(pos_a, len(da), pos_b, len(db), delta)
        audit = ExpWindowAudit(n=len(self._window), disparity=round(d_hat, 4),
                               lcb=round(lcb, 4), blocked=lcb > self.threshold,
                               delta=delta, attr=self.attr)
        self._window = []
        return audit
