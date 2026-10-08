"""Bloque E · E2.2: planificador por ranking del LLC (Fig. 4.21) con las adaptaciones de P3."""
from moav_hr.core.equidad_roles import RegistroE, e_paridad_errores, u_rol
from moav_hr.core.planificador import PlanificadorLLC
from moav_hr.core.theory import TheoryBase, theory_key

ACC = ("ADVANCE", "REJECT")
SI = {"skills_match": 2, "exp_band": "senior", "edu": "Licenciatura", "seniority_ok": True}
OK, NO = {"calificado": True}, {"calificado": False}


def _u(a, sf):
    return 1.0 if (a == "ADVANCE") == sf["calificado"] else 0.0


def _reg(b, si, a, sf, veces=1):
    for _ in range(veces):
        b.registrar_llc(si, a, sf, _u(a, sf))


def test_orden_fig_4_21_y_plan_de_una_teoria():
    b = TheoryBase()
    _reg(b, SI, "ADVANCE", OK, 3)        # U=1, P=3
    _reg(b, SI, "REJECT", NO, 1)         # U=1, P=1
    _reg(b, SI, "ADVANCE", NO, 1)        # U=0
    d = PlanificadorLLC(b, ACC).planificar(SI, "TBO", "REJECT")
    assert d.motivo == "celda" and d.accion == "ADVANCE" and not d.es_azar
    assert [f["u_tarea"] for f in d.candidatas] == [1.0, 1.0, 0.0]
    assert d.candidatas[0]["p"] == 3                       # a igual U, mayor P


def test_otra_si_no_es_aplicable():
    b = TheoryBase()
    _reg(b, dict(SI, skills_match=3), "ADVANCE", OK)
    d = PlanificadorLLC(b, ACC).planificar(SI, "BIO", "REJECT")
    assert d.motivo == "azar_no_probada" and d.accion == "ADVANCE" and d.es_azar


def test_regla_de_validez_y_azar_por_capa():
    b = TheoryBase()
    _reg(b, SI, "ADVANCE", NO)           # única teoría de la celda, u_tarea = 0
    p = PlanificadorLLC(b, ACC)
    d = p.planificar(SI, "TBO", "ADVANCE")
    assert d.validez_aplicada and d.motivo == "azar_no_probada" and d.accion == "REJECT"
    _reg(b, SI, "REJECT", OK)            # también falló REJECT: ya se probaron las dos
    d = p.planificar(SI, "BIO", "ADVANCE")
    assert d.validez_aplicada and d.motivo == "azar_bio" and d.accion == "ADVANCE"
    d = p.planificar(SI, "WIO", "REJECT")                   # en WIO no se explora
    assert d.motivo == "azar_bio" and d.accion == "REJECT"


def test_celda_vacia_en_wio_usa_el_operador_bio():
    d = PlanificadorLLC(TheoryBase(), ACC).planificar(SI, "WIO", "REJECT")
    assert d.motivo == "azar_bio" and d.accion == "REJECT" and not d.validez_aplicada


def test_respaldo_por_similitud_solo_con_la_celda_vacia_y_activado():
    b = TheoryBase()
    _reg(b, dict(SI, edu="Maestría"), "ADVANCE", OK)        # 3 de 4 atributos: coseno 0,75
    assert PlanificadorLLC(b, ACC).planificar(SI, "WIO", "REJECT").motivo == "azar_bio"
    d = PlanificadorLLC(b, ACC, respaldo_similitud=True).planificar(SI, "WIO", "REJECT")
    assert d.motivo == "similitud" and d.accion == "ADVANCE" and not d.es_azar
    _reg(b, SI, "REJECT", NO)                                # la celda deja de estar vacía
    d = PlanificadorLLC(b, ACC, respaldo_similitud=True).planificar(SI, "WIO", "ADVANCE")
    assert d.motivo == "celda" and d.accion == "REJECT"


def test_desacuerdo_fig_4_21_frente_al_alg_4_7():
    b = TheoryBase()
    _reg(b, SI, "REJECT", NO, 1)                             # U=1, (P,K) = (1,1): P/K = 1
    _reg(b, SI, "ADVANCE", OK, 4)                            # U=1, P=4
    _reg(b, SI, "ADVANCE", NO, 1)                            # → ADVANCE/OK queda (4,5)
    d = PlanificadorLLC(b, ACC).planificar(SI, "TBO", "REJECT")
    assert d.accion == "ADVANCE"                             # Fig. 4.21: mayor P
    assert d.desacuerdo_alg47 is not None                    # Alg. 4.7: mayor P/K → REJECT


def test_equidad_cambia_el_orden_solo_con_estimacion():
    assert e_paridad_errores([("A", True)] * 4 + [("B", True)] * 5, m_min=5) is None
    e = e_paridad_errores([("A", True)] * 5 + [("B", False)] * 5, m_min=5)
    assert e == 0.0
    assert u_rol(1.0, None, 0.5) == (1.0, False)
    assert u_rol(1.0, 0.0, 0.5) == (0.5, True)
    b = TheoryBase()
    _reg(b, SI, "ADVANCE", OK, 3)
    _reg(b, SI, "REJECT", NO, 1)
    reg = RegistroE()
    ta = next(t for t in b.theories if t.a == "ADVANCE")
    for i in range(10):                                      # ADVANCE: errores solo en un grupo
        reg.registrar(theory_key(ta, b.q), "AR" if i % 2 else "no-AR", bool(i % 2))
    p1 = PlanificadorLLC(b, ACC, alpha=1.0, registro_e=reg).planificar(SI, "TBO", "REJECT")
    p05 = PlanificadorLLC(b, ACC, alpha=0.5, registro_e=reg).planificar(SI, "TBO", "REJECT")
    assert p1.accion == "ADVANCE" and p05.accion == "REJECT" and p05.equidad_usada
