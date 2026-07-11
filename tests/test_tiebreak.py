"""A5+A10 — desempate determinista en la selección de teorías (Def. 4)."""
from moav_hr.core.theory import Theory, TheoryBase


def _t(sf_val: int, p: int, k: int, u: float) -> Theory:
    return Theory(si={"x": 1}, a="A", sf={"r": sf_val}, p=p, k=k, u=u)


def test_empate_total_gana_la_mas_reciente():
    base = TheoryBase()
    t_vieja = _t(1, p=2, k=4, u=0.8)
    t_nueva = _t(2, p=2, k=4, u=0.8)      # (u, p, k) idénticos
    base.add(t_vieja)
    base.add(t_nueva)
    sel = base.select({"x": 1})
    assert sel is t_nueva                  # recencia descendente


def test_determinismo_en_corridas_repetidas():
    resultados = []
    for _ in range(5):
        base = TheoryBase()
        for i in range(3):
            base.add(_t(i, p=1, k=2, u=0.5))
        resultados.append(base.select({"x": 1}).sf["r"])
    assert len(set(resultados)) == 1


def test_add_estampa_id_y_recencia_monotonos():
    base = TheoryBase()
    a, b = _t(1, 1, 1, 0.5), _t(2, 1, 1, 0.5)
    base.add(a)
    base.add(b)
    assert (a.id, b.id) == (1, 2)
    assert a.created_at < b.created_at
