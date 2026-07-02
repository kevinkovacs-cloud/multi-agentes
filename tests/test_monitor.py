"""
Monitor de Utilidad de Equidad Ω (v13 §2.4) — ejercita explícitamente sus tres puntos
de actuación: auditoría por ventana (región 4), gate de evolución (región 7) y
aprobación de compartición (Def. 9). Antes estos métodos existían sin llamadores.
"""
from moav_hr.core.agent import MOACVAgent
from moav_hr.core.monitor import FairnessUtilityMonitor


def _rec(group: str, decision: str, tq: float = 0.8) -> dict:
    return {"origin_group": group, "gender": "F", "decision": decision,
            "true_qual": tq, "score": tq, "bias_risk": "low"}


def test_audit_window_marca_ventana_con_disparidad():
    """Región 4: |Δ(W)| > umbral ⇒ la ventana queda marcada (blocked)."""
    mon = FairnessUtilityMonitor(disparity_threshold=0.075)
    records = [_rec("A", "ADVANCE") for _ in range(5)] + \
              [_rec("B", "REJECT") for _ in range(5)]          # Δ = 1.0
    audit = mon.audit_window(records)
    assert audit.blocked
    assert audit.disparity == 1.0
    assert audit.fair == round(1.0 - audit.disparity, 4)


def test_audit_window_no_marca_ventana_equitativa():
    mon = FairnessUtilityMonitor(disparity_threshold=0.075)
    records = [_rec("A", "ADVANCE") for _ in range(5)] + \
              [_rec("B", "ADVANCE") for _ in range(5)]         # Δ = 0.0
    audit = mon.audit_window(records)
    assert not audit.blocked
    assert audit.disparity == 0.0
    assert audit.fair == 1.0


def test_gate_evolution_por_reputacion():
    """Región 7: un agente con reputación de equidad < τ no progresa de estado."""
    mon = FairnessUtilityMonitor(tau=0.8)
    bajo = MOACVAgent("Bajo", "matcher")
    bajo.record_window_fairness(0.5)                            # r = 0.5 < τ
    assert not mon.gate_evolution(bajo)
    alto = MOACVAgent("Alto", "matcher")
    alto.record_window_fairness(0.95)                           # r = 0.95 ≥ τ
    assert mon.gate_evolution(alto)
    virgen = MOACVAgent("SinHistoria", "matcher")               # sin ventanas: r = 1.0
    assert mon.gate_evolution(virgen)


def test_approve_sharing_por_reputacion():
    """Def. 9: Ω acepta la compartición solo si la reputación del emisor alcanza τ."""
    mon = FairnessUtilityMonitor(tau=0.8)
    donante = MOACVAgent("Donante", "matcher")
    donante.record_window_fairness(0.7)                         # r = 0.7 < τ
    assert not mon.approve_sharing(donante)
    donante.record_window_fairness(0.95)                        # r = (0.7+0.95)/2 = 0.825 ≥ τ
    assert mon.approve_sharing(donante)
