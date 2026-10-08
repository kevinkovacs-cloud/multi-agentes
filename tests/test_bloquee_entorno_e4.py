"""Bloque E · E4: el código de las estrategias cumple las reglas pre-registradas del entorno."""
import pytest

from moav_hr.instances.hr import entorno as E
from moav_hr.instances.hr.estrategias_llc import explicar, extraer

SEMILLA, SEMILLA_DOC = 20261008, 20261009
CASOS = [c for capa, n in (("BIO", 60), ("TBO", 100), ("WIO", 100))
         for c in E.generar_escenario(capa, n, SEMILLA)]
HECHOS = {"resultado": "REJECT", "ventana": "BIO-W1", "trace_id": "TRC-T-1",
          "si_matcher": {"skills_match": 1, "exp_band": "junior", "edu": "Licenciatura",
                         "seniority_ok": False},
          "teoria": {"id": 3, "p": 2, "k": 4, "u": 0.5},
          "dictamen": {"brecha_dp": 0.2, "lcb": 0.0, "tau_b": 0.075, "accion": "LIBERAR"}}


def test_parser_percepcion_y_resultado_por_plantilla_cumplen_la_regla_7():
    vistas = set()
    for caso in CASOS:
        doc, idx, defecto = E.generar_documento(caso, SEMILLA_DOC)
        si = E.percibir_documento(doc)
        assert si == E.CELDAS_PARSER[idx]
        assert set(si) == {"formato", "estructura", "etiquetas"}       # DE-4: sin valores
        for estrategia in E.ESTRATEGIAS_PARSER:
            sf = E.validar_perfil(extraer(estrategia, doc))
            esperado = E.RESULTADO_PARSER[idx][estrategia]
            if defecto and esperado == "completo":
                esperado = "parcial"
            assert (sf["completitud"], sf["fuga"]) == (esperado, False)
        vistas.add(idx)
    assert vistas == set(range(len(E.CELDAS_PARSER)))


def test_el_shape_del_perfil_detecta_fuga_y_campos_faltantes():
    sf = E.validar_perfil({"skills": ["Python"], "exp": 3, "edu": "Maestría", "origen": "SY"})
    assert sf["fuga"] and E.u_parser(sf) == 0.0
    sf = E.validar_perfil({"skills": ["Python"], "exp": None, "edu": None})
    assert (sf["completitud"], sf["faltan"]) == ("parcial", ["exp", "edu"])
    assert E.u_parser(sf) == 0.5


@pytest.mark.parametrize("tipo", ["avanza", "rechaza", "deriva"])
@pytest.mark.parametrize("dest", list(E.DESTINATARIOS))
@pytest.mark.parametrize("motivos", ["uno", "varios"])
def test_explainer_completitud_contra_el_grafo_cumple_la_regla_10(tipo, dest, motivos):
    si = {"tipo": tipo, "destinatario": dest, "motivos": motivos}
    g = E.grafo_hechos_caso(HECHOS)
    for estrategia in E.ESTRATEGIAS_EXPLAINER:
        el = explicar(estrategia, HECHOS)
        assert set(el) == E.ELEMENTOS_POR_ESTRATEGIA[estrategia]
        assert E.verificar_explicacion(el, si, g)["completa"] == \
            (E.requisitos_explicacion(si) <= E.ELEMENTOS_POR_ESTRATEGIA[estrategia])


def test_explainer_un_hecho_que_no_coincide_con_el_grafo_la_hace_incompleta():
    si = {"tipo": "rechaza", "destinatario": "regulador", "motivos": "uno"}
    el = explicar("regulatoria", HECHOS)
    el["secuencia_trazable"] = el["secuencia_trazable"].replace("TRC-T-1", "TRC-otro")
    v = E.verificar_explicacion(el, si, E.grafo_hechos_caso(HECHOS))
    assert not v["completa"] and v["inconsistentes"] == ["secuencia_trazable"]


def test_auditor_la_regla_no_puede_derivar_con_ventanas_de_20():
    assert E.lcb_maxima_ventana(10, 0.05) < 0.075
    todo_o_nada = [("AR", "ADVANCE")] * 10 + [("no-AR", "REJECT")] * 10
    si = E.situacion_ventana(todo_o_nada, 0.075, 0.05)
    assert si == {"n_por_grupo": "10-49", "brecha": "alta", "lcb_supera_tau_b": False}
    assert E.regla_certificada(si) == "LIBERAR"
    assert E.situacion_ventana([("AR", "ADVANCE")] * 60 + [("no-AR", "REJECT")] * 60,
                               0.075, 0.05)["lcb_supera_tau_b"]


def test_descripcion_e4_coincide_con_las_reglas():
    d = E.describir_entorno_e4(0.075, 0.05, 20)
    assert d["parser"]["por_grupo"]["AR"]["p_completo_mejor_estrategia"] == 0.9
    assert not d["auditor"]["puede_derivar"]
    assert len(d["explainer"]["celdas"]) == 12
