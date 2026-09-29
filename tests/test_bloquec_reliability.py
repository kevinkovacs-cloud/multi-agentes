"""
Bloque C · C2 — la confiabilidad no cambia de denominador al fusionar.

reliability = (P+1)/(K_propio+2). Antes usaba el K expuesto, que tras una fusión pasa
a ser el K de toda la celda: una teoría (P, K_propio) = (3, 4) caía de 4/6 a 4/12 sin
evidencia nueva, solo por fusionarse con una variante similar.
Provisorio hasta la decisión 2 del director (semántica de P y K).
"""
import pytest

from moav_hr.core.sharing import cooperate
from moav_hr.core.theory import Theory, TheoryBase

S = {"perfil": "p1"}


def test_confiabilidad_se_conserva_tras_fusionar_con_variante_similar():
    a = TheoryBase()
    a.add(Theory(si=dict(S), a="X", sf={"r": "ok"}, p=3, k=4, u=0.5))
    b = TheoryBase()
    b.add(Theory(si=dict(S), a="X", sf={"r": "mal"}, p=1, k=6, u=0.5))  # misma celda, otra variante
    assert a.theories[0].reliability == pytest.approx(4 / 6)
    cooperate(a, b)
    ok = next(t for t in a.theories if t.sf == {"r": "ok"})
    assert (ok.p, ok.k_own, ok.k) == (3, 4, 10)       # K expuesto = K de la celda
    assert ok.reliability == pytest.approx(4 / 6)     # antes: 4/12


def test_sin_fusiones_el_valor_no_cambia():
    for p, k in [(0, 0), (1, 1), (3, 4), (99, 99)]:
        t = Theory(si={}, a="A", sf={}, p=p, k=k)
        assert t.k == t.k_own
        assert t.reliability == pytest.approx((p + 1) / (k + 2))
    t = Theory(si={}, a="A", sf={})
    for ok in (True, False, True, True):
        t.reinforce(ok)
    assert (t.p, t.k, t.k_own) == (3, 4, 4)
    assert t.reliability == pytest.approx(4 / 6)
