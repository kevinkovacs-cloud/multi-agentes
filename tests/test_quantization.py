"""
A1 — equivalencia por cuantización: relación de equivalencia real (transitiva) y
fusión de bases asociativa por celdas.
"""
from moav_hr.core.theory import (Theory, TheoryBase, equivalent, q_canonical, q_grid,
                                 theories_equal, theories_similar)
from moav_hr.core.sharing import ShareReport, _merge


# ---------- (i) ≅ es relación de equivalencia ----------

def test_equivalencia_qcanonical():
    a, b, c = {"x": 1, "y": 2}, {"y": 2, "x": 1}, {"x": 1, "y": 2}
    assert equivalent(a, a)                      # reflexiva
    assert equivalent(a, b) == equivalent(b, a)  # simétrica (orden de claves no importa)
    assert equivalent(a, b) and equivalent(b, c) and equivalent(a, c)  # transitiva


def test_equivalencia_qgrid():
    q = q_grid(lambda s: [s["v"]], h=1.0)
    a, b, c = {"v": 2.1}, {"v": 2.2}, {"v": 2.3}
    assert q(a) == q(a)
    assert (q(a) == q(b)) == (q(b) == q(a))
    assert q(a) == q(b) and q(b) == q(c) and q(a) == q(c)


# ---------- (ii) el contraejemplo del esquema viejo, como test del nuevo ----------

def test_transitividad_donde_el_esquema_viejo_fallaba():
    """Con sim≥δ, a~b y b~c no implicaban a~c (solapamiento encadenado). Con Q es
    igualdad de celdas: a≅b ∧ b≅c ⇒ a≅c, siempre."""
    q = q_grid(lambda s: [s["v"]], h=1.0)
    a, b, c = {"v": 1.8}, {"v": 2.0}, {"v": 2.2}   # vecinos encadenados
    if equivalent(a, b, q) and equivalent(b, c, q):
        assert equivalent(a, c, q)
    # y en la misma celda, la cadena completa es equivalente
    a2, b2, c2 = {"v": 2.1}, {"v": 2.2}, {"v": 2.3}
    assert equivalent(a2, b2, q) and equivalent(b2, c2, q) and equivalent(a2, c2, q)


def test_iguales_y_similares_por_celda():
    t1 = Theory(si={"x": 1}, a="A", sf={"r": 1}, p=1, k=1)
    t2 = Theory(si={"x": 1}, a="A", sf={"r": 1}, p=3, k=4)
    t3 = Theory(si={"x": 1}, a="A", sf={"r": 2}, p=1, k=1)
    assert theories_equal(t1, t2) and not theories_equal(t1, t3)
    assert theories_similar(t1, t3) and not theories_similar(t1, t2)


# ---------- (iii) fusión de 3 bases asociativa ----------

def _t(cell_x: int, sf_val: int, p: int, k: int) -> Theory:
    return Theory(si={"x": cell_x}, a="A", sf={"r": sf_val}, p=p, k=k)


def _fuse(x: TheoryBase, y: TheoryBase) -> TheoryBase:
    out = TheoryBase()
    out.replace_all(_merge(x, y, ShareReport("cooperation", accepted=True)))
    return out


def _multiset(base: TheoryBase) -> set:
    return frozenset((q_canonical(t.si), t.a, q_canonical(t.sf), t.p, t.k)
                     for t in base.theories)


def test_fusion_de_tres_bases_es_asociativa():
    A, B, C = TheoryBase(), TheoryBase(), TheoryBase()
    A.add(_t(1, sf_val=1, p=1, k=2))                      # celda 1, variante 1
    B.add(_t(1, sf_val=1, p=2, k=3))                      # igual a la de A
    B.add(_t(1, sf_val=2, p=1, k=4))                      # similar (otra variante)
    C.add(_t(1, sf_val=2, p=2, k=5))                      # igual a la variante 2 de B
    C.add(_t(2, sf_val=1, p=1, k=1))                      # celda nueva
    izq = _fuse(_fuse(A, B), C)
    der = _fuse(A, _fuse(B, C))
    assert _multiset(izq) == _multiset(der)
    # valores esperados: celda 1 → var1 (P=3, K=14), var2 (P=3, K=14); celda 2 → (P=1, K=1)
    esperado = {
        (q_canonical({"x": 1}), "A", q_canonical({"r": 1}), 3, 14),
        (q_canonical({"x": 1}), "A", q_canonical({"r": 2}), 3, 14),
        (q_canonical({"x": 2}), "A", q_canonical({"r": 1}), 1, 1),
    }
    assert _multiset(izq) == esperado


# ---------- (iv) grupo de 3 similares ----------

def test_grupo_de_tres_similares_conserva_P_y_suma_K():
    A, B, C = TheoryBase(), TheoryBase(), TheoryBase()
    A.add(_t(1, sf_val=1, p=1, k=2))
    B.add(_t(1, sf_val=2, p=2, k=3))
    C.add(_t(1, sf_val=3, p=3, k=4))
    fused = _fuse(_fuse(A, B), C)
    assert len(fused) == 3
    por_sf = {t.sf["r"]: t for t in fused.theories}
    assert (por_sf[1].p, por_sf[2].p, por_sf[3].p) == (1, 2, 3)   # cada una su P
    assert all(t.k == 2 + 3 + 4 for t in fused.theories)          # K = suma del grupo
