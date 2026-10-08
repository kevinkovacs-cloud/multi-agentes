"""Bloque E · E2.3–E2.5: motor del ciclo LLC, estadísticas, capas y regla de evolución."""
from moav_hr.core.audit.trail import AuditTrail
from moav_hr.core.ciclo_llc import AgenteLLC, ConfigCiclo, MotorLLC, evaluar_regla
from moav_hr.core.estadisticas import EstadisticasLLC
from moav_hr.core.lifecycle import Layer, MaturityState, capa_llc, active_layer
from moav_hr.core.monitor import FairnessMonitor
from moav_hr.core.theory import TheoryBase, violaciones_invariante_llc
from moav_hr.instances.hr import entorno
from moav_hr.instances.hr.roles_llc import RolMatcherLLC


def _cfg(**kw):
    base = dict(n_intervalo=4, ciclos_por_capa={"BIO": 8, "TBO": 8, "WIO": 8}, rce=25, rtn=20,
                acciones_orden=("ADVANCE", "REJECT"))
    base.update(kw)
    return ConfigCiclo(**base)


def _motor(cfg, semilla=1):
    ag = AgenteLLC("SemanticMatcher", "matcher")
    m = MotorLLC(ag, RolMatcherLLC(0.1, semilla), FairnessMonitor(tau=0.8), cfg,
                 trail=AuditTrail("TRC-T"))
    esc = {c: entorno.generar_escenario(c, 8, semilla) for c in ("BIO", "TBO", "WIO")}
    return ag, m, esc


def test_mapa_de_capas_del_llc_sin_tocar_el_anterior():
    assert capa_llc(MaturityState.BORN) == Layer.BIO
    assert capa_llc(MaturityState.NOVATO) == Layer.TBO
    assert capa_llc(MaturityState.TRAINED) == Layer.WIO          # p. 62 (G3)
    assert active_layer(MaturityState.TRAINED) == Layer.TBO        # modo anterior intacto


def test_regla_de_evolucion():
    r = evaluar_regla(15, 12, 9, 20, False, True, 25, 20)
    assert r["pct_cea"] == 25.0 and r["promueve"] and r["pct_tn"] is None
    assert not evaluar_regla(14, 12, 0, 20, False, True, 25, 20)["promueve"]
    assert not evaluar_regla(15, 12, 0, 20, False, False, 25, 20)["promueve"]   # gate de Ω
    r = evaluar_regla(15, 12, 5, 20, True, True, 25, 20)
    assert r["pct_tn"] == 25.0 and not r["promueve"]                          # %TN > %RTN
    assert evaluar_regla(3, 0, 0, 20, False, True, 25, 20)["pct_cea"] == 300.0   # max(CE_0, 1)


def test_cada_ciclo_recorre_las_siete_regiones_en_orden():
    ag, m, esc = _motor(_cfg())
    m.correr_capa("BIO", esc["BIO"])
    regiones = [e.region for e in m.trail.events]
    assert len(regiones) == 7 * m.ciclo
    assert all(regiones[i:i + 7] == [1, 2, 3, 4, 5, 6, 7] for i in range(0, len(regiones), 7))
    assert violaciones_invariante_llc(ag.theories) == []
    r7 = [e for e in m.trail.events if e.region == 7 and e.detail["evaluada"]]
    assert len(r7) == len(m.evaluaciones) and all(e.detail["ciclo_capa"] % 4 == 0 for e in r7)


def test_el_estado_se_gana_y_sin_regla_no_hay_promocion():
    ag, m, esc = _motor(_cfg(rce=10_000))              # regla imposible: nunca promueve
    assert ag.maturity == MaturityState.BORN
    res = m.correr(esc)
    assert ag.maturity == MaturityState.BORN and res["estado_final"] == "Born"
    assert [c["capa"] for c in res["capas"]] == ["BIO"] and m.ciclo == 8   # no pasa de capa
    ag2, m2, esc2 = _motor(_cfg(rce=-10_000))         # regla trivial: promueve al primer cierre
    m2.monitor.tau = 0.0
    res2 = m2.correr(esc2)
    assert res2["estado_final"] == "Mature" and m2.ciclo == 12      # 4 ciclos por capa
    assert [e["estado_despues"] for e in m2.evaluaciones] == ["Novice", "Trained", "Mature"]


def test_la_respuesta_del_entorno_llega_despues_de_la_accion():
    ag, m, esc = _motor(_cfg())
    m.correr_capa("BIO", esc["BIO"])
    for reg, caso in zip(m.ciclos, esc["BIO"]):
        assert reg["sf"] == {"calificado": caso.calificado}
        assert reg["u_tarea"] == (1.0 if (reg["accion"] == "ADVANCE") == caso.calificado
                                  else 0.0)


def test_estadisticas_de_la_region_6():
    b = TheoryBase()
    b.registrar_llc({"s": 1}, "ADVANCE", {"c": 1}, 1.0)
    b.registrar_llc({"s": 2}, "ADVANCE", {"c": 0}, 0.0)
    st = EstadisticasLLC()
    st.registrar_ciclo("x", "nueva", 1.0, True, False, False)
    st.registrar_ciclo("y", "nueva", 0.0, False, True, False)
    f = st.instantanea(b)
    assert f["ciclos_exitosos"] == 1 and f["azares"] == 1 and f["planes"] == 1
    assert f["teorias_por_intervalo_u"] == [0, 0, 0, 1] and f["teorias_exitosas"] == 1
    assert f["situaciones"] == 2 and f["teorias_nuevas"] == 2
