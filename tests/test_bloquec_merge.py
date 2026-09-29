"""
Bloque C · C1 — `_merge` conmutativa (y asociativa) en u.

La u de la variante fusionada es el promedio ponderado por evidencia
u = Σ k_own·u / Σ k_own. Antes quedaba la u de la PRIMERA fuente, de modo que
cooperate(A,B) ≠ cooperate(B,A) y la selección elegía acciones distintas según el
orden. Con los datos de abajo la regla vieja elegía X en un orden e Y en el otro.
Regla provisoria hasta la decisión 2 del director (semántica de P y K).
"""
import pytest

from moav_hr.core.sharing import cooperate
from moav_hr.core.theory import Theory, TheoryBase

S = {"perfil": "p1"}   # situación común: todas las teorías caen en la misma Q(Si)


def _base(specs):
    """specs: [(accion, sf, p, k, u)] → TheoryBase con la cuantización por defecto."""
    b = TheoryBase()
    for a, sf, p, k, u in specs:
        b.add(Theory(si=dict(S), a=a, sf={"r": sf}, p=p, k=k, u=u))
    return b


def _A():
    return _base([("X", "ok", 1, 1, 0.9), ("Y", "ok", 1, 1, 0.5)])


def _B():
    return _base([("X", "ok", 2, 9, 0.2), ("Y", "ok", 5, 9, 0.6)])


def _C():
    # X tiene dos variantes (ok / mal): celda con teorías similares
    return _base([("X", "ok", 1, 3, 0.4), ("X", "mal", 0, 2, 0.3), ("Z", "ok", 2, 4, 0.7)])


def _sig(base):
    """Multiconjunto (celda, variante, p, k_own, u), ordenado por clave."""
    q = base.q
    return sorted(((q(t.si), t.a), q(t.sf), t.p, t.k_own, t.u) for t in base.theories)


def _assert_same(s1, s2):
    assert len(s1) == len(s2)
    for (c1, v1, p1, k1, u1), (c2, v2, p2, k2, u2) in zip(s1, s2):
        assert (c1, v1, p1, k1) == (c2, v2, p2, k2)
        assert u1 == pytest.approx(u2, abs=1e-12)


def test_cooperacion_conmutativa_en_u_y_en_la_seleccion():
    a1, b1 = _A(), _B()
    cooperate(a1, b1)            # A ⊕ B
    a2, b2 = _A(), _B()
    cooperate(b2, a2)            # B ⊕ A
    _assert_same(_sig(a1), _sig(b2))
    _assert_same(_sig(a1), _sig(b1))   # la base de la cooperación es común
    # u ponderada: X = (1·0.9 + 9·0.2)/10 = 0.27 ; Y = (1·0.5 + 9·0.6)/10 = 0.59
    us = {t.a: t.u for t in a1.theories}
    assert us["X"] == pytest.approx(0.27, abs=1e-12)
    assert us["Y"] == pytest.approx(0.59, abs=1e-12)
    # la selección ya no depende del orden de la fusión
    assert a1.select(S).a == b2.select(S).a == "Y"


def test_fusion_asociativa_en_p_kown_u():
    a, b, c = _A(), _B(), _C()
    cooperate(a, b)
    cooperate(a, c)              # (A ⊕ B) ⊕ C
    izq = _sig(a)
    a, b, c = _A(), _B(), _C()
    cooperate(b, c)
    cooperate(a, b)              # A ⊕ (B ⊕ C)
    der = _sig(a)
    _assert_same(izq, der)


def test_variante_de_una_sola_fuente_conserva_su_u():
    # 0.1·3/3 != 0.1 en punto flotante: la u de una sola teoría se conserva literal
    a = _base([("X", "ok", 1, 3, 0.1)])
    b = _base([("W", "ok", 2, 3, 0.7)])
    cooperate(a, b)
    us = {t.a: t.u for t in a.theories}
    assert us["X"] == 0.1
    assert us["W"] == 0.7
