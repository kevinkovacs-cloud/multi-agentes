"""Bloque E · DE-8: entorno simulado por capa (reglas pre-registradas) y DE-4."""
from moav_hr.instances.hr import entorno
from moav_hr.instances.hr.parser_agent import build_si, normalize_profile

PROTEGIDOS = {"gender", "origin", "origin_group", "age", "grupo", "genero", "origen", "edad"}


def test_escenarios_deterministas_y_dentro_del_catalogo():
    for capa, n in (("BIO", 60), ("TBO", 100), ("WIO", 100)):
        a = entorno.generar_escenario(capa, n, 7)
        assert a == entorno.generar_escenario(capa, n, 7)
        cat = entorno.CATALOGO[capa]
        for c in a:
            si = build_si(normalize_profile(c.candidato))
            assert si["edu"] in cat["edu"] and si["exp_band"] in cat["banda"]
            assert si["skills_match"] in cat["skills"]


def test_grupos_balanceados_por_intervalo_e_independientes():
    casos = entorno.generar_escenario("TBO", 100, 3)
    for i in range(0, 100, 20):
        grupos = [c.grupo for c in casos[i:i + 20]]
        assert grupos.count("AR") == 10 and grupos.count("no-AR") == 10


def test_atributo_protegido_fuera_de_si_y_de_las_acciones():
    for c in entorno.generar_escenario("WIO", 40, 1):
        si = build_si(normalize_profile(c.candidato))
        assert not (set(si) & PROTEGIDOS)
        assert c.candidato.origin not in map(str, si.values())
        assert entorno.operador_bio_matcher(si) in entorno.ACCIONES


def test_respuesta_del_entorno_en_la_region_3():
    casos = entorno.generar_escenario("BIO", 20, 5)
    for c in casos:
        assert entorno.observar(c, "BIO", 0.1, 5) == {"calificado": c.calificado}
    wio = entorno.generar_escenario("WIO", 100, 5)
    obs = [entorno.observar(c, "WIO", 0.1, 5) for c in wio]
    assert obs == [entorno.observar(c, "WIO", 0.1, 5) for c in wio]      # determinista
    assert [entorno.observar(c, "WIO", 0.0, 5) for c in wio] == \
        [{"calificado": c.calificado} for c in wio]                      # ε = 0 → la verdad


def test_operador_bio_imperfecto_en_3_de_8_celdas():
    d = entorno.describir_entorno(0.1)["BIO"]
    malas = [f for f in d["celdas"] if f["accion_bio"] != f["mejor_accion"]]
    assert len(malas) == 3 and d["n_celdas"] == 8
