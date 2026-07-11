"""
Monitor de Utilidad de Equidad Ω — componente genérico del LLC (v13 §2.4, Def. 1).

Supervisa la dimensión de equidad de la utilidad operativa en tres puntos del ciclo de
vida de los demás agentes:
  - región 4: audita que fair(W) no se degrade respecto de un umbral de disparidad.
  - región 7: condiciona la evolución (un agente con baja reputación de equidad no progresa).
  - compartición: pondera la transferencia según la reputación rⱼ ≥ τ (Def. 9).

CERTIFICACIÓN (B6+A8): con `certified=True`, el bloqueo y el gate usan la COTA INFERIOR
DE CONFIANZA (Hoeffding, core/stats.py) en lugar de la estimación puntual. Garantía:
P(bloqueo | Δ=0) ≤ δ (falsos bloqueos controlados por construcción) y la promoción de
estado exige evidencia, no una media puntual. El modo puntual (default) conserva el
comportamiento del demo del video.

Es agnóstico del dominio: el criterio de equidad y el atributo protegido son configurables.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from moav_hr.core import fairness
from moav_hr.core import stats


@dataclass
class WindowAudit:
    disparity: float       # |Δ(W)| (estimación puntual)
    fair: float            # 1 − |Δ(W)|
    acc: float
    u_op: float
    blocked: bool          # puntual: disparity > umbral · certificado: lcb > umbral
    criterion: str
    attr: str
    lcb: Optional[float] = None    # cota inferior de confianza de |Δ| (si certified)
    certified: bool = False        # True si el bloqueo usó LCB (garantía FPR ≤ δ)
    delta: float = 0.05            # nivel de confianza del certificado


class FairnessUtilityMonitor:
    """Agente auditor Ω."""

    def __init__(self, criterion: str = "demographic_parity", attr: str = "origin_group",
                 disparity_threshold: float = 0.075, tau: float = 0.8, alpha: float = 0.5,
                 d0: float = 0.0):
        if criterion not in fairness.CRITERIA:
            raise ValueError(f"criterio debe ser uno de {fairness.CRITERIA}")
        self.criterion = criterion
        self.attr = attr
        self.disparity_threshold = disparity_threshold   # umbral de bloqueo (región 4)
        self.tau = tau                                    # umbral de reputación (Def. 9)
        self.alpha = alpha
        self.d0 = d0                                      # umbral de diversidad (Def. 11/C2)

    # región 4
    def audit_window(self, records: list[dict], certified: bool = False,
                     delta: float = 0.05) -> WindowAudit:
        """
        Audita la ventana. Puntual (default): bloquea si |Δ̂| > τ_b — sin garantía de
        falsos positivos. Certificado: bloquea si LCB_δ(|Δ|) > τ_b — bajo H₀ (Δ=0),
        P(bloqueo) ≤ δ. El certificado exige exactamente 2 grupos en la ventana.
        """
        d = fairness.disparity(records, self.attr, self.criterion)
        lcb = None
        if certified:
            lcb = self._lcb_dp(records, delta)
            blocked = lcb > self.disparity_threshold
        else:
            blocked = abs(d) > self.disparity_threshold
        return WindowAudit(
            disparity=abs(d),
            fair=fairness.fair_window(records, self.attr, self.criterion),
            acc=fairness.acc_window(records),
            u_op=fairness.u_op(records, self.attr, self.criterion, self.alpha),
            blocked=blocked,
            criterion=self.criterion, attr=self.attr,
            lcb=lcb, certified=certified, delta=delta)

    def _lcb_dp(self, records: list[dict], delta: float) -> float:
        """LCB de |p_a − p_b| sobre las tasas de avance por grupo (Hoeffding, δ/2 c/u)."""
        groups: dict[str, list[str]] = {}
        for r in records:
            groups.setdefault(str(r[self.attr]), []).append(r["decision"])
        if len(groups) != 2:
            raise ValueError("el certificado requiere exactamente 2 grupos en la ventana")
        (da, db) = groups.values()
        pos_a = sum(1 for d in da if d in fairness.POSITIVE)
        pos_b = sum(1 for d in db if d in fairness.POSITIVE)
        return stats.lcb_abs_diff_rates(pos_a, len(da), pos_b, len(db), delta)

    # compartición (Def. 9)
    def approve_sharing(self, donor) -> bool:
        return donor.reputation() >= self.tau

    # región 7 — Def. 12 (evolución condicionada, A8)
    def gate_evolution(self, agent, certified: bool = False, m: int = 5,
                       delta: float = 0.05) -> bool:
        """
        El agente progresa solo si su reputación de equidad alcanza τ_r.

        Puntual (default): media de fair(W) sobre las últimas m ventanas ≥ τ.
        Certificado (Def. 12): LCB_δ de esa media ≥ τ — exige historia suficiente
        (sin ventanas observadas no hay certificado: devuelve False).
        """
        if not certified:
            return agent.reputation() >= self.tau
        window_values = agent._fair_history[-m:]
        n = len(window_values)
        if n == 0:
            return False
        mean = sum(window_values) / n
        return (mean - stats.hoeffding_halfwidth(n, delta)) >= self.tau
