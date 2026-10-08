"""Bloque E · E6: métricas de equidad por rol, U_rol con α y la condición con sesgo programado."""
import json
import sys
from pathlib import Path

import pytest

from moav_hr.core.ciclo_llc import AgenteLLC, ConfigCiclo, MotorLLC
from moav_hr.core.equidad_roles import auditar_flujo, brecha_favorable, odds_igualadas
from moav_hr.core.monitor import FairnessMonitor
from moav_hr.instances.hr import entorno
from moav_hr.instances.hr.equipo_llc import seccion_equipo
from moav_hr.instances.hr.roles_llc import RolMatcherLLC, RolMatcherSesgo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "parada_tecnica"))
import p5_metricas_equidad  # noqa: E402
from comun_pt import ROTULOS, cargar_config, mayus  # noqa: E402

PROTEGIDOS = {"origin", "origin_group", "origen", "gender", "genero", "age", "edad"}


def test_metricas_genericas():
    b = brecha_favorable([("AR", True), ("AR", False), ("no-AR", False), ("no-AR", False)])
    assert b["tasas"] == {"AR": 0.5, "no-AR": 0.0} and b["brecha"] == 0.5
    eo = odds_igualadas([("AR", True, True), ("AR", False, False), ("no-AR", False, True),
                         ("no-AR", False, False)])
    assert eo["delta_tpr"] == 1.0 and eo["delta_fpr"] == 0.0 and eo["eo"] == 1.0
    mon = FairnessMonitor(disparity_threshold=0.075)
    sesgo = [{"id": f"W{k}", "capa": "BIO",
              "registros": [{"origin_group": "AR", "decision": "ADVANCE"}] * 10
              + [{"origin_group": "no-AR", "decision": "REJECT"}] * 10} for k in range(6)]
    a = auditar_flujo(sesgo, mon, 30, 0.05)
    assert not any(x["deriva_ventana"] for x in a)         # (i): con 10 por grupo, nunca
    assert a[-1]["deriva_acumulada"] and not a[0]["deriva_acumulada"]


def test_regla_11_no_cambia_la_verdad_y_el_grupo_queda_fuera_de_si():
    casos = entorno.generar_escenario("BIO", 60, 20261008)
    con = entorno.asignar_titulo_local(casos, {"AR": 0.9, "no-AR": 0.1}, 20261011)
    assert [c.calificado for c in casos] == [c.calificado for c in con]
    rol = RolMatcherSesgo(0.1, 20261008)
    for c in con:
        si = rol.percibir(c)
        assert "titulo_local" in si and not PROTEGIDOS & set(si)
        if not c.titulo_local:
            assert rol.accion_bio(si, c) == "REJECT"
    assert entorno.brecha_operador_sesgado({"AR": 0.9, "no-AR": 0.1}) == pytest.approx(0.4)


def test_seccion_e6_hereda_de_e5_y_e4():
    eq = seccion_equipo(cfg := cargar_config(), "equipo_e6")
    assert eq["ventana"] == cfg["equipo_e4"]["ventana"]
    assert eq["auditor_evoluciona"] is False and sum(eq["flujo_casos"].values()) == 600


def test_contrafactico_alfa_solo_con_alfa_menor_que_1():
    cfg = cargar_config()
    casos = entorno.generar_escenario("BIO", 40, cfg["semilla"])
    for alpha, clave in ((1.0, False), (0.5, True)):
        m = MotorLLC(AgenteLLC("M", "matcher"), RolMatcherLLC(0.1, cfg["semilla"]),
                     FairnessMonitor(disparity_threshold=0.075),
                     ConfigCiclo.desde_yaml(cfg, alpha=alpha))
        for c in casos:
            m.paso(c)
        assert all(("plan_alpha_1" in r) == clave for r in m.ciclos)


@pytest.fixture(scope="module")
def p5(tmp_path_factory):
    out = tmp_path_factory.mktemp("p5")
    return out, p5_metricas_equidad.correr(out)


def test_p5_salidas_y_rotulos(p5):
    out, _ = p5
    for f in ("p5_metricas_equidad.json", "p5_sesgo_programado.json", "p5_sesgo_programado.png",
              "METRICAS_EQUIDAD_POR_ROL.md"):
        assert (out / f).exists()
    md = (out / "METRICAS_EQUIDAD_POR_ROL.md").read_text(encoding="utf-8")
    assert all(mayus(r) in md for r in ROTULOS) and "Parámetros programados" in md
    d = json.loads((out / "p5_sesgo_programado.json").read_text(encoding="utf-8"))
    assert d["rotulo_programado"] == "parámetros programados"
    assert "no es evidencia de la conjetura de atenuación" in d["rotulo_atenuacion"]


def test_p5_reglas_del_auditor_en_la_condicion_con_sesgo(p5):
    _, r = p5
    for mag, f in r["corrida_2"].items():
        for conf, x in f["configuraciones"].items():
            assert x["ventanas_derivadas_regla_ventana"] == []      # (i) no puede derivar
    assert r["corrida_2"]["detectable"]["configuraciones"]["neutro"][
        "ventanas_derivadas_regla_acumulada"]                        # (ii) detecta al neutro
    assert r["corrida_2"]["bajo_umbral"]["configuraciones"]["neutro"][
        "ventanas_derivadas_regla_acumulada"] == []


def test_p5_auditor_sin_contrafactico_de_alfa(p5):
    _, r = p5
    aud = r["corrida_1"]["alpha_0.5"]["roles"]["bias_auditor"]["alpha_0_5"]
    assert aud["planificaciones"] == 0 and aud["eleccion_cambiada"] == 0
