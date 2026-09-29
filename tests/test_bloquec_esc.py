"""
Bloque C · C5 — Δ^esc: disparidad de la tasa de escalamiento entre grupos.

ESCALATE_HUMAN ∈ fairness.POSITIVE, así que la paridad demográfica cuenta el
escalamiento como favorable y no ve que un grupo sea derivado a revisión humana más
que otro. escalation_disparity lo mide (misma forma que demographic_parity_delta).
"""
from moav_hr.core import fairness


def _recs(grupo, n, decision):
    return [{"origin_group": grupo, "decision": decision} for _ in range(n)]


def test_cero_con_tasas_iguales():
    recs = (_recs("A", 3, "ESCALATE_HUMAN") + _recs("A", 7, "ADVANCE")
            + _recs("B", 6, "ESCALATE_HUMAN") + _recs("B", 14, "REJECT"))
    assert fairness.escalation_disparity(recs, "origin_group") == 0.0


def test_caso_simpson_ventanas_90_10_y_10_90():
    # ventana 1: 90 de A y 10 de B, TODOS escalados; ventana 2: 10 de A y 90 de B, ninguno
    w1 = _recs("A", 90, "ESCALATE_HUMAN") + _recs("B", 10, "ESCALATE_HUMAN")
    w2 = _recs("A", 10, "ADVANCE") + _recs("B", 90, "ADVANCE")
    # dentro de cada ventana la tasa es igual entre grupos...
    assert fairness.escalation_disparity(w1, "origin_group") == 0.0
    assert fairness.escalation_disparity(w2, "origin_group") == 0.0
    # ...pero agregando: A = 90/100, B = 10/100 → 0.8
    assert fairness.escalation_disparity(w1 + w2, "origin_group") == 0.8
    # y la paridad demográfica no lo ve (ESCALATE_HUMAN cuenta como favorable)
    assert fairness.demographic_parity_delta(w1 + w2, "origin_group") == 0.0


def test_simetria_y_menos_de_dos_grupos():
    a = _recs("A", 2, "ESCALATE_HUMAN") + _recs("A", 8, "ADVANCE")
    b = _recs("B", 5, "ESCALATE_HUMAN") + _recs("B", 5, "ADVANCE")
    assert fairness.escalation_disparity(a + b, "origin_group") == \
        fairness.escalation_disparity(b + a, "origin_group") == 0.3
    assert fairness.escalation_disparity(a, "origin_group") == 0.0
    assert fairness.escalation_disparity([], "origin_group") == 0.0
