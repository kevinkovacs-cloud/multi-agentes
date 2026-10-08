"""Bloque E · E5: reglas de E5 como opciones (E4 no cambia), equipos que comparten y L-3."""
import json
import sys
from pathlib import Path

import pytest

from moav_hr.instances.hr.equipo_llc import ROLES, EquipoLLC, seccion_equipo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "parada_tecnica"))
import e4_muestreo  # noqa: E402
import p3_equipos_dag  # noqa: E402
from comun_pt import ROTULOS, cargar_config, mayus  # noqa: E402
from preregistro_e5 import L3_FUENTE, formulas_l3  # noqa: E402


def test_formulas_l3_reproducen_las_tablas_l16_y_l17():
    for x in L3_FUENTE.values():
        f = formulas_l3(x["ce_min"], x["ce_max"], x["ce_prom"], x["tn_max"], x["tn_colab"],
                        x["tn_prom"])
        calc = (f["pct_cea"], f["pct_rce"], f["pct_tna"], f["pct_rtn"])
        assert all(abs(c - p) < 1.0 for c, p in zip(calc, x["publicado"]))


def test_seccion_e5_hereda_de_e4_y_pisa_solo_lo_suyo():
    cfg = cargar_config()
    e4, e5 = seccion_equipo(cfg, "equipo_e4"), seccion_equipo(cfg, "equipo_e5",
                                                              cfg["equipo_e5"]["equipos"]["C"])
    assert e5["ventana"] == e4["ventana"] and e5["flujo"] == e4["flujo"]
    assert e5["semilla_casos"] == cfg["equipo_e5"]["equipos"]["C"]["casos"]
    assert "auditor_evoluciona" not in e4 and e5["auditor_evoluciona"] is False


@pytest.fixture(scope="module")
def p3(tmp_path_factory):
    out = tmp_path_factory.mktemp("p3")
    return out, p3_equipos_dag.correr(out)


def test_reglas_de_e5_en_el_equipo(p3):
    _, res = p3
    m = res["metricas"]
    for e in ("A", "B", "B0", "BC", "C"):
        aud = m[e]["bias_auditor"]
        assert not aud["evoluciona"] and aud["evaluaciones"] == [] and aud["estado_final"] == "Born"
        assert "azar_no_probada" not in m[e]["matcher"]["motivos"].get("WIO", {})
        assert "azar_no_probada" not in m[e]["parser"]["motivos"].get("WIO", {})
    for e in ("N",):
        for r in ROLES:
            assert set(m[e][r]["motivos"].get("BIO", {})) <= {"operador_bio"}
            assert m[e][r]["promociones"] == []


def test_explainer_de_e5_percibe_tipo_y_destinatario_y_explora_en_wio():
    cfg = cargar_config()
    eq = EquipoLLC("X", cfg, "equipo_e5", cfg["equipo_e5"]["equipos"]["A"])
    eq.correr()
    m = eq.motores["explainer"]
    assert all(set(r["si"]) == {"tipo", "destinatario"} for r in m.ciclos)
    assert m.planificador.capas_exploracion == ("BIO", "TBO", "WIO")
    assert eq.motores["matcher"].planificador.capas_exploracion == ("BIO", "TBO")
    assert all(ce.si_explainer_entorno["motivos"] in ("uno", "varios") for ce in eq.casos)


def test_comparticion_y_salidas_de_p3(p3):
    out, res = p3
    assert all(x["aceptada"] and x["invariante_receptor"] for x in res["colaboracion"])
    for c in res["cooperacion"].values():
        for x in c["intentos"]:
            if x["aceptada"]:
                assert x["invariante_receptor"] and x["invariante_donante"]
    assert set(res["l3"]) == set(res["config_e5"]["l3"]["roles"])
    for f in ("p3_equipos.json", "p3_equipos.md", "p3_maduracion_equipos.png"):
        assert (out / f).exists()
    md = (out / "p3_equipos.md").read_text(encoding="utf-8")
    assert all(mayus(r) in md for r in ROTULOS)
    d = json.loads((out / "p3_equipos.json").read_text(encoding="utf-8"))
    assert d["rotulos"] == ROTULOS


def test_b_y_b0_procesan_los_mismos_casos(p3):
    _, res = p3
    lt = res["lineas_de_tiempo"]
    assert [x["ventana"] for x in lt["B"]] == [x["ventana"] for x in lt["B0"]] == \
        [x["ventana"] for x in lt["BC"]]


def test_muestreo_e4(tmp_path):
    r = e4_muestreo.correr(tmp_path)
    c = r["flujo_e4"]["conteo"]
    assert c["AR"]["n"] == c["no-AR"]["n"] == 130
    assert r["semillas_extra"]["n"] == cargar_config()["equipo_e5"]["muestreo_e4"]["semillas_extra"]
    assert (tmp_path / "e4_muestreo_calificados.md").exists()
