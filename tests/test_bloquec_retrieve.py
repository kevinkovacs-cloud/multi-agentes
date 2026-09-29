"""
Bloque C · C9 — desempate de TheoryRetriever.retrieve coherente con TheoryBase.select.

retrieve (el planificador que corre en el pipeline) ordenaba por (−U, −P, K) sin
recencia ni id: el sort estable dejaba primero la teoría más ANTIGUA ante empates
exactos, mientras select (Def. 4, A5+A10) elige la más RECIENTE. Ahora ambos usan
(−U, −P, K, −created_at, id).
"""
from moav_hr.core.retrieval import TheoryRetriever
from moav_hr.core.theory import Theory, TheoryBase

S = {"perfil": "p1", "exp": "senior"}


def _base_con_empate():
    base = TheoryBase()
    base.add(Theory(si=dict(S), a="VIEJA", sf={"r": 1}, p=2, k=3, u=0.6))   # created_at=1
    base.add(Theory(si=dict(S), a="NUEVA", sf={"r": 2}, p=2, k=3, u=0.6))   # created_at=2
    return base


def test_empate_exacto_gana_la_mas_reciente():
    base = _base_con_empate()
    top = TheoryRetriever(base, delta=0.6).retrieve(S)
    assert top[0].a == "NUEVA"


def test_retrieve_coincide_con_select():
    base = _base_con_empate()
    base.add(Theory(si=dict(S), a="PEOR", sf={"r": 3}, p=1, k=3, u=0.4))
    base.add(Theory(si=dict(S), a="OTRA_EMPATADA", sf={"r": 4}, p=2, k=3, u=0.6))
    # mismas candidatas (similitud 1 con S): el primero de retrieve es el de select
    assert TheoryRetriever(base, delta=0.6, top_k=10).retrieve(S)[0] is base.select(S)
    assert base.select(S).a == "OTRA_EMPATADA"        # la más reciente del empate
