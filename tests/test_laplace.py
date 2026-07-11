"""A2 — suavizado de Laplace en la confiabilidad: (P+1)/(K+2)."""
import pytest

from moav_hr.core.agent import MOACVAgent
from moav_hr.core.theory import Theory


def test_k_cero_da_media_prior():
    assert Theory(si={"x": 1}, a="A", sf={"r": 1}).reliability == 0.5


def test_valores_canonicos():
    assert Theory(si={}, a="A", sf={}, p=1, k=1).reliability == pytest.approx(2 / 3)
    assert Theory(si={}, a="A", sf={}, p=99, k=99).reliability == pytest.approx(100 / 101)


def test_converge_a_p_sobre_k():
    t = Theory(si={}, a="A", sf={}, p=900, k=1000)
    assert t.reliability == pytest.approx(0.9, abs=0.001)


def test_monotonia_en_p():
    k = 10
    rels = [Theory(si={}, a="A", sf={}, p=p, k=k).reliability for p in range(k + 1)]
    assert all(rels[i] < rels[i + 1] for i in range(len(rels) - 1))


def test_learn_sin_u_usa_reliability():
    ag = MOACVAgent("X", "matcher")
    t = ag.learn({"x": 1}, "A", {"r": 1}, success=True)      # p=1,k=1 → 2/3
    assert t.u == pytest.approx(2 / 3)
    t2 = ag.learn({"x": 1}, "A", {"r": 1}, success=True)     # refuerza: p=2,k=2 → 3/4
    assert t2 is t and t2.u == pytest.approx(3 / 4)


def test_learn_con_u_explicita_se_respeta():
    ag = MOACVAgent("X", "matcher")
    t = ag.learn({"x": 1}, "A", {"r": 1}, success=True, u=0.9)
    assert t.u == 0.9
