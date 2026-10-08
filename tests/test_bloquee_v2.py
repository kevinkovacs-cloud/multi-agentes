"""Bloque E · pre-registro v2: gate por evidencia de sesgo, U basada en la acción, evaluación acumulada."""
from moav_hr.core import stats
from moav_hr.core.audit.trail import AuditTrail
from moav_hr.core.ciclo_llc import AgenteLLC, ConfigCiclo, MotorLLC
from moav_hr.core.monitor import FairnessMonitor
from moav_hr.core.planificador import PlanificadorLLC
from moav_hr.core.theory import TheoryBase, violaciones_invariante_llc
from moav_hr.instances.hr import entorno
from moav_hr.instances.hr.roles_llc import RolMatcherLLC

SI = {"skills_match": 0, "exp_band": "junior", "edu": "Licenciatura", "seniority_ok": False}
OK, NO = {"calificado": True}, {"calificado": False}


def _acierto(t):
    return (t.a == "ADVANCE") == t.sf["calificado"]


def _rec(grupo, decision):
    return {"origin_group": grupo, "decision": decision}


def test_gate_evidencia_de_sesgo():
    mon = FairnessMonitor(disparity_threshold=0.075)
    sesgado = [_rec("AR", "ADVANCE")] * 40 + [_rec("no-AR", "REJECT")] * 40
    r = mon.gate_evidencia_sesgo(sesgado, n_cierres=3, delta=0.05)
    assert r["niega"] and r["brecha"] == 1.0
    assert r["lcb"] == round(stats.lcb_abs_diff_rates(40, 40, 0, 40, 0.05 / 3), 4)
    parejo = [_rec(g, d) for g in ("AR", "no-AR") for d in ("ADVANCE", "REJECT") * 10]
    assert mon.gate_evidencia_sesgo(parejo, 3)["aprueba"]
    assert mon.gate_evidencia_sesgo([_rec("AR", "ADVANCE")] * 5, 3)["aprueba"]   # un grupo
    chico = [_rec("AR", "ADVANCE")] * 10 + [_rec("no-AR", "REJECT")] * 10
    assert mon.gate_evidencia_sesgo(chico, 3)["aprueba"]       # n = 10: ninguna brecha alcanza


def test_u_basada_en_la_accion_control_de_la_traza():
    b = TheoryBase()
    b.registrar_llc(SI, "ADVANCE", OK, 1.0)
    for _ in range(6):
        b.registrar_llc(SI, "ADVANCE", NO, 0.0)
    u = b.recalcular_u_accion(SI, "ADVANCE", _acierto)
    assert u == 2 / 9                                           # (1 + 1) / (7 + 2)
    assert {t.u for t in b.theories} == {2 / 9}                 # igual para las variantes
    assert violaciones_invariante_llc(b) == []
    pl = PlanificadorLLC(b, ("ADVANCE", "REJECT"), validez_minima=0.5, validez_estricta=False)
    d = pl.planificar(SI, "BIO", "REJECT")
    assert d.validez_aplicada and d.motivo == "azar_no_probada" and d.accion == "REJECT"
    pl_v1 = PlanificadorLLC(b, ("ADVANCE", "REJECT"))           # v1: u > 0 → sigue ADVANCE
    assert pl_v1.planificar(SI, "BIO", "REJECT").accion == "ADVANCE"


def test_un_acierto_aislado_no_deja_u_igual_a_1():
    b = TheoryBase()
    b.registrar_llc(SI, "ADVANCE", OK, 1.0)
    assert b.recalcular_u_accion(SI, "ADVANCE", _acierto) == 2 / 3


def _motor(cfg, semilla=1):
    ag = AgenteLLC("SemanticMatcher", "matcher")
    m = MotorLLC(ag, RolMatcherLLC(0.1, semilla), FairnessMonitor(tau=0.8), cfg,
                 trail=AuditTrail("TRC-T"))
    esc = {c: entorno.generar_escenario(c, 12, semilla) for c in ("BIO", "TBO", "WIO")}
    return ag, m, esc


def test_evaluacion_acumulada_y_gate_v2_en_el_motor():
    cfg = ConfigCiclo(n_intervalo=4, ciclos_por_capa={"BIO": 12, "TBO": 12, "WIO": 12},
                      rce=10_000, rtn=20, acciones_orden=("ADVANCE", "REJECT"),
                      evaluacion="acumulada_en_la_capa", gate="evidencia_de_sesgo",
                      utilidad_teoria="accion", validez="u_mayor_o_igual_0_5")
    ag, m, esc = _motor(cfg)
    m.correr_capa("BIO", esc["BIO"])
    ev = m.evaluaciones
    assert [e["ciclo_capa"] for e in ev] == [4, 8, 12]
    acum = 0
    for e, j in zip(ev, (4, 8, 12)):
        acum = sum(r["exitoso"] for r in m.ciclos[:j])
        assert e["ce_a"] == acum                                 # acumulado desde la capa
        assert e["evidencia_sesgo"]["n_cierres"] == 3
        assert e["gate_omega"] == e["evidencia_sesgo"]["aprueba"]
    assert violaciones_invariante_llc(ag.theories) == []
    for t in ag.theories.theories:                               # U(Si, A) igual en la celda
        celda = [x for x in ag.theories.theories if x.si == t.si and x.a == t.a]
        assert len({x.u for x in celda}) == 1


def test_la_config_v1_reproduce_los_defaults():
    from pathlib import Path
    from moav_hr.core.runlog import load_config
    repo = Path(__file__).resolve().parents[1]
    v1 = ConfigCiclo.desde_yaml(load_config(str(repo / "configs" / "parada_tecnica_v1.yaml")))
    v2 = ConfigCiclo.desde_yaml(load_config(str(repo / "configs" / "parada_tecnica.yaml")))
    assert (v1.version, v1.gate, v1.utilidad_teoria, v1.evaluacion) == \
        ("v1", "puntual", "u_tarea", "por_intervalo")
    assert (v2.version, v2.gate, v2.utilidad_teoria, v2.evaluacion, v2.validez) == \
        ("v2", "evidencia_de_sesgo", "accion", "acumulada_en_la_capa", "u_mayor_o_igual_0_5")
    for campo in ("n_intervalo", "ciclos_por_capa", "rce", "rtn", "umbral_exitoso", "m_min"):
        assert getattr(v1, campo) == getattr(v2, campo)          # sin cambios
