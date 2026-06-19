"""Tests del núcleo genérico: teorías (Def. 3/4), compartición (Def. 7/8/9), fairness (Def. 5/6/10)."""
from moav_hr.core.theory import Theory, TheoryBase
from moav_hr.core.sharing import cooperate, collaborate
from moav_hr.core.retrieval import similarity
from moav_hr.core import fairness


def test_seleccion_def4():
    tb = TheoryBase()  # sim exacto, δ=1.0
    tb.add(Theory(si={"x": 1}, a="advance", sf={"r": "ok"}, p=5, k=10, u=0.8))
    tb.add(Theory(si={"x": 1}, a="reject", sf={"r": "no"}, p=8, k=10, u=0.8))
    assert tb.select({"x": 1}).a == "reject"   # empate en U → mayor P


def test_invariante_p_menor_igual_k():
    import pytest
    with pytest.raises(ValueError):
        Theory(si={}, a="A", sf={}, p=5, k=3)


def test_equivalencia_por_cuantizacion():
    a = {"exp_band": "mid", "edu": "Maestría", "skills_match": 2, "seniority_ok": True}
    assert similarity(a, dict(a)) >= 0.6
    assert similarity(a, {"exp_band": "junior", "edu": "x", "skills_match": 0, "seniority_ok": False}) < 0.6


def test_cooperacion_def7():
    bi, bj = TheoryBase(), TheoryBase()
    bi.add(Theory(si={"x": 1}, a="A", sf={"r": 1}, p=2, k=3))
    bj.add(Theory(si={"x": 1}, a="A", sf={"r": 1}, p=4, k=5))   # igual
    rep = cooperate(bi, bj)
    t = bi.theories[0]
    assert (t.p, t.k) == (6, 8) and rep.reinforced == 1


def test_colaboracion_def8_y_reputacion_def9():
    recep, colab = TheoryBase(), TheoryBase()
    colab.add(Theory(si={"x": 1}, a="A", sf={"r": 1}, p=5, k=6))
    rep = collaborate(recep, colab, donor_reputation=0.5, tau=0.8)   # reputación baja
    assert not rep.accepted and len(recep) == 0
    rep2 = collaborate(recep, colab, donor_reputation=0.9, tau=0.8)  # reputación alta
    assert rep2.accepted and len(recep) == 1


def test_fairness_y_amplificacion_def10():
    amp = fairness.amplification(0.067, 0.014)
    assert amp.regime == "attenuation" and amp.mu is not None and amp.mu < 1
    amp0 = fairness.amplification(0.0, 0.05)
    assert amp0.regime == "bias_introduced" and amp0.mu is None
    recs = [{"origin_group": "AR", "decision": "ADVANCE", "true_qual": 0.9, "score": 0.9, "bias_risk": "low"},
            {"origin_group": "no-AR", "decision": "REJECT", "true_qual": 0.9, "score": 0.6, "bias_risk": "high"}]
    assert 0.0 <= fairness.fair_window(recs, "origin_group", "demographic_parity") <= 1.0
