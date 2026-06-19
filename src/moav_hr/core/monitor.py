"""
Monitor de Utilidad de Equidad Ω — componente genérico del LLC (v13 §2.4, Def. 1).

Supervisa la dimensión de equidad de la utilidad operativa en tres puntos del ciclo de
vida de los demás agentes:
  - región 4: audita que fair(W) no se degrade respecto de un umbral de disparidad.
  - región 7: condiciona la evolución (un agente con baja reputación de equidad no progresa).
  - compartición: pondera la transferencia según la reputación rⱼ ≥ τ (Def. 9).

Es agnóstico del dominio: el criterio de equidad y el atributo protegido son configurables.
"""
from __future__ import annotations
from dataclasses import dataclass

from moav_hr.core import fairness


@dataclass
class WindowAudit:
    disparity: float       # |Δ(W)|
    fair: float            # 1 − |Δ(W)|
    acc: float
    u_op: float
    blocked: bool          # disparity > umbral
    criterion: str
    attr: str


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
    def audit_window(self, records: list[dict]) -> WindowAudit:
        delta = fairness.disparity(records, self.attr, self.criterion)
        return WindowAudit(
            disparity=abs(delta),
            fair=fairness.fair_window(records, self.attr, self.criterion),
            acc=fairness.acc_window(records),
            u_op=fairness.u_op(records, self.attr, self.criterion, self.alpha),
            blocked=abs(delta) > self.disparity_threshold,
            criterion=self.criterion, attr=self.attr)

    # compartición (Def. 9)
    def approve_sharing(self, donor) -> bool:
        return donor.reputation() >= self.tau

    # región 7
    def gate_evolution(self, agent) -> bool:
        """El agente progresa solo si su reputación de equidad alcanza τ."""
        return agent.reputation() >= self.tau
