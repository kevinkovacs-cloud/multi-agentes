"""B3 — disparidad firmada y detector de inversión de signo."""
import pytest

from moav_hr.core import fairness


def _rec(group: str, advanced: bool, tq: float = 0.9) -> dict:
    return {"origin_group": group, "gender": "F", "true_qual": tq,
            "decision": "ADVANCE" if advanced else "REJECT",
            "score": 0.8, "bias_risk": "low"}


def test_signo_positivo_desfavorece_al_no_referencia():
    records = [_rec("AR", True)] * 4 + [_rec("no-AR", True)] * 1 + [_rec("no-AR", False)] * 3
    d = fairness.disparity_signed(records, "origin_group", "demographic_parity",
                                  reference_group="AR")
    assert d == pytest.approx(0.75)          # 1.00 − 0.25 > 0 → desfavorece a no-AR


def test_signo_estable_con_referencia_fija_ante_permutacion():
    records = [_rec("AR", True)] * 2 + [_rec("no-AR", False)] * 2
    d1 = fairness.disparity_signed(records, "origin_group", "demographic_parity", "AR")
    d2 = fairness.disparity_signed(list(reversed(records)), "origin_group",
                                   "demographic_parity", "AR")
    assert d1 == d2 == 1.0


def test_inversion_detectada():
    # entrada desfavorecía a no-AR (+0.30); salida favorece a no-AR (−0.20) con piso 0.1
    assert fairness.is_inversion(0.30, -0.20, floor=0.1)
    assert not fairness.is_inversion(0.30, 0.10, floor=0.1)     # mismo signo
    assert not fairness.is_inversion(0.30, -0.05, floor=0.1)    # magnitud bajo el piso


def test_referencia_inexistente_es_error():
    with pytest.raises(ValueError):
        fairness.disparity_signed([_rec("AR", True)], "origin_group",
                                  "demographic_parity", "no-AR")
