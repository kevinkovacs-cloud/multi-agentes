"""A7 — equalized odds con dos componentes (ΔTPR y ΔFPR)."""
from moav_hr.core import fairness


def _rec(group: str, qualified: bool, advanced: bool) -> dict:
    return {"origin_group": group, "gender": "F",
            "true_qual": 0.9 if qualified else 0.5,
            "decision": "ADVANCE" if advanced else "REJECT",
            "score": 0.8, "bias_risk": "low"}


def test_fpr_mayor_que_tpr_ya_no_se_subestima():
    """Caso construido: TPR igual entre grupos (Δ=0) pero FPR muy dispar —
    el delta viejo (solo TPR) daba 0.0; el nuevo reporta la disparidad real."""
    records = (
        # positivos: ambos grupos avanzan a todos sus calificados → ΔTPR = 0
        [_rec("A", True, True)] * 4 + [_rec("B", True, True)] * 4 +
        # negativos: grupo A avanza a 3/4 no calificados; grupo B a 0/4 → ΔFPR = 0.75
        [_rec("A", False, True)] * 3 + [_rec("A", False, False)] +
        [_rec("B", False, False)] * 4
    )
    comp = fairness.equalized_odds_components(records, "origin_group")
    assert comp["tpr_delta"] == 0.0
    assert comp["fpr_delta"] == 0.75
    assert fairness.equalized_odds_delta(records, "origin_group") == 0.75


def test_tpr_sigue_dominando_cuando_corresponde():
    records = (
        [_rec("A", True, True)] * 4 +
        [_rec("B", True, True)] * 1 + [_rec("B", True, False)] * 3 +   # ΔTPR = 0.75
        [_rec("A", False, False)] * 2 + [_rec("B", False, False)] * 2  # ΔFPR = 0
    )
    assert fairness.equalized_odds_delta(records, "origin_group") == 0.75


def test_sin_negativos_en_dos_grupos_fpr_es_cero():
    records = [_rec("A", True, True)] * 3 + [_rec("B", True, False)] * 3
    comp = fairness.equalized_odds_components(records, "origin_group")
    assert comp["fpr_delta"] == 0.0 and comp["tpr_delta"] == 1.0
