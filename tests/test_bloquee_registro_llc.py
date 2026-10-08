"""Bloque E · E2.1: registro de teorías del LLC (Fig. 4.13) e invariante ΣP = K."""
import random

from moav_hr.core.agent import MOACVAgent, TBOLayer
from moav_hr.core.sharing import collaborate, cooperate
from moav_hr.core.theory import TheoryBase, violaciones_invariante_llc

SI = {"s": 1}
OK, NO = {"calificado": True}, {"calificado": False}


def test_reglas_de_la_figura_4_13():
    b = TheoryBase()
    t1, tipo = b.registrar_llc(SI, "ADVANCE", OK, 1.0)
    assert tipo == "nueva" and (t1.p, t1.k) == (1, 1)               # sin similares: P=1, K=1
    t1b, tipo = b.registrar_llc(SI, "ADVANCE", OK, 1.0)
    assert tipo == "igual" and t1b is t1 and (t1.p, t1.k) == (2, 2)  # igual: P+1, K+1
    t2, tipo = b.registrar_llc(SI, "ADVANCE", NO, 0.0)
    assert tipo == "similar" and (t2.p, t2.k) == (1, 3)             # similar: P=1, K=K_sim+1
    assert (t1.p, t1.k) == (2, 3)                                   # y K+1 en la similar
    b.registrar_llc(SI, "ADVANCE", OK, 1.0)                         # igual otra vez
    assert (t1.p, t1.k, t2.p, t2.k) == (3, 4, 1, 4)                 # K+1 también en la similar
    t3, tipo = b.registrar_llc(SI, "REJECT", OK, 0.0)               # otra acción: otra celda
    assert tipo == "nueva" and (t3.p, t3.k) == (1, 1)
    assert violaciones_invariante_llc(b) == []


def _base_aleatoria(seed, n=80):
    rng = random.Random(seed)
    b = TheoryBase()
    for _ in range(n):
        si = {"s": rng.randint(0, 2)}
        a = rng.choice(["ADVANCE", "REJECT"])
        sf = {"calificado": rng.random() < 0.6}
        b.registrar_llc(si, a, sf, 1.0 if (a == "ADVANCE") == sf["calificado"] else 0.0)
    return b


def test_invariante_tras_registrar_cooperar_y_colaborar():
    for seed in range(5):
        a, b = _base_aleatoria(seed), _base_aleatoria(100 + seed)
        assert violaciones_invariante_llc(a) == [] and violaciones_invariante_llc(b) == []
        a2, b2 = _base_aleatoria(seed), _base_aleatoria(100 + seed)
        assert cooperate(a2, b2).accepted
        assert violaciones_invariante_llc(a2) == [] and violaciones_invariante_llc(b2) == []
        r = _base_aleatoria(200 + seed)
        assert collaborate(r, _base_aleatoria(300 + seed)).accepted
        assert violaciones_invariante_llc(r) == []
        r.registrar_llc({"s": 1}, "ADVANCE", OK, 1.0)          # seguir aprendiendo tras fusionar
        assert violaciones_invariante_llc(r) == []


def test_colaboracion_sigue_el_algoritmo_4_10_en_modo_llc():
    rec, col = TheoryBase(), TheoryBase()
    rec.registrar_llc(SI, "ADVANCE", OK, 1.0)                       # receptor: (P,K) = (1,1)
    for _ in range(3):
        col.registrar_llc(SI, "ADVANCE", NO, 0.0)                   # colaborador: similar (3,3)
    collaborate(rec, col)
    por_sf = {t.sf["calificado"]: (t.p, t.k) for t in rec.theories}
    # Alg. 4.10: cada variante conserva su P; K = K_receptor + K_colaborador
    assert por_sf == {True: (1, 4), False: (3, 4)}


def test_learn_llc_del_agente_y_learn_anterior_intacto():
    ag = MOACVAgent("M", "matcher", tbo=TBOLayer(training_runs=0))
    t, tipo = ag.learn_llc(SI, "ADVANCE", OK, 1.0)
    assert tipo == "nueva" and t.u == 1.0
    viejo = MOACVAgent("V", "matcher")
    tv = viejo.learn(SI, "ADVANCE", OK, success=False)
    assert (tv.p, tv.k) == (0, 1)                                   # semántica anterior: P = aciertos
