"""Bloque E · E4: equipo DAG con todos los roles en el modo LLC, su ABox, SHACL y SPARQL."""
import copy
import json
import sys
from pathlib import Path

import pytest
from rdflib import Literal
from rdflib.namespace import XSD

from moav_hr.core.ciclo_llc import AgenteLLC, ConfigCiclo, MotorLLC
from moav_hr.core.compartir_llc import compartir
from moav_hr.core.lifecycle import MaturityState
from moav_hr.core.monitor import FairnessMonitor
from moav_hr.core.ontology import queries_llc as Q
from moav_hr.core.ontology.abox import theory_iri
from moav_hr.core.ontology.abox_llc import abox_equipo, ciclo_iri
from moav_hr.core.ontology.ns import MOACV, PROV
from moav_hr.core.ontology.sharing_rdf import procedencia_compartida
from moav_hr.core.ontology.shapes_llc import validar_llc
from moav_hr.instances.hr import entorno
from moav_hr.instances.hr.equipo_llc import ROLES, EquipoLLC
from moav_hr.instances.hr.estrategias_llc import extraer
from moav_hr.instances.hr.roles_llc import RolMatcherLLC

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "parada_tecnica"))
from comun_pt import cargar_config  # noqa: E402

PROTEGIDOS = {"origin", "origin_group", "origen", "nacionalidad", "gender", "genero", "sexo",
              "age", "edad"}
SI_POR_ROL = {"parser": {"formato", "estructura", "etiquetas"},
              "matcher": {"skills_match", "exp_band", "edu", "seniority_ok"},
              "bias_auditor": {"n_por_grupo", "brecha", "lcb_supera_tau_b"},
              "explainer": {"tipo", "destinatario", "motivos"}}


@pytest.fixture(scope="module")
def equipo():
    eq = EquipoLLC("T", cargar_config())
    eq.correr()
    return eq


def _decisiones(eq):
    return [{"trace_id": ce.trace_id, "resultado": ce.decision_final,
             "ciclos": {r: reg["ciclo"] for r, reg in ce.ciclos.items()}} for ce in eq.casos]


@pytest.fixture(scope="module")
def abox(equipo):
    return abox_equipo([(r, equipo.agentes[r], equipo.motores[r]) for r in ROLES],
                       _decisiones(equipo))


def test_paso_reproduce_correr_capa_hasta_la_promocion():
    cfg = cargar_config()
    c = ConfigCiclo.desde_yaml(cfg)
    casos = entorno.generar_escenario("BIO", c.ciclos_por_capa["BIO"], cfg["semilla"])

    def motor():
        return MotorLLC(AgenteLLC("M", "matcher"), RolMatcherLLC(0.1, cfg["semilla"]),
                        FairnessMonitor(tau=0.8, disparity_threshold=0.075), c)
    a, b = motor(), motor()
    res = a.correr_capa("BIO", casos)
    for caso in casos[:res["ciclos"]]:
        b.paso(caso)
    clave = ("ciclo", "accion", "motivo", "sf", "registro", "p", "k", "u", "exitoso")
    assert [tuple(r[k] for k in clave) for r in a.ciclos] == \
        [tuple(r[k] for k in clave) for r in b.ciclos]
    assert [e["promueve"] for e in a.evaluaciones] == [e["promueve"] for e in b.evaluaciones]
    assert a.agente.maturity == b.agente.maturity


def test_equipo_recorre_el_dag_por_ventana_con_langgraph(equipo):
    n = sum(cargar_config()["ciclo_de_vida"]["ciclos_por_capa"].values())
    assert len(equipo.casos) == n and len(equipo.ventanas) == n // 20
    ev = equipo.trail.events
    assert sum(e.action == "pipeline_start" for e in ev) == len(equipo.ventanas)
    assert sum(e.action == "final_decision" for e in ev) == n
    for r in ROLES:                                    # siete regiones por ciclo de cada rol
        regiones = [e.region for e in ev if e.agent == equipo.agentes[r].name]
        assert regiones == list(range(1, 8)) * equipo.motores[r].ciclo


def test_atributo_protegido_fuera_de_si_y_de_a_en_todos_los_roles(equipo):
    for r in ROLES:
        for reg in equipo.motores[r].ciclos:
            assert set(reg["si"]) == SI_POR_ROL[r]
            assert not PROTEGIDOS & set(reg["si"])
            assert reg["accion"] in equipo.roles[r].acciones


def test_auditor_la_accion_es_siempre_la_regla_certificada(equipo):
    for reg in equipo.motores["bias_auditor"].ciclos:
        assert reg["motivo"] == "regla_certificada" and reg["accion"] == reg["accion_bio"]
        assert reg["acierto_bio"] == reg["exitoso"]


def test_ce0_del_parser_es_el_contrafactico_del_operador_bio(equipo):
    distintos = 0
    for ce in equipo.casos:
        reg = ce.ciclos["parser"]
        sf_bio = entorno.validar_perfil(extraer(entorno.OPERADOR_BIO_PARSER, ce.documento))
        assert reg["acierto_bio"] == (entorno.u_parser(sf_bio) > 0.75)
        distintos += reg["accion"] != reg["accion_bio"]
    assert distintos > 0


def test_abox_del_equipo_conforma_con_sigma_p_igual_k(equipo, abox):
    conforma, texto, _ = validar_llc(abox)
    assert conforma, texto
    teorias = sum(len(equipo.agentes[r].theories) for r in ROLES)
    assert len(set(abox.subjects(predicate=MOACV.celda))) == teorias


def test_shacl_detecta_sigma_p_distinto_de_k_y_atributo_en_si(equipo, abox):
    g = copy.deepcopy(abox)
    t = next(iter(g.subjects(predicate=MOACV.celda)))
    p = g.value(t, MOACV.P)
    g.set((t, MOACV.P, Literal(int(p) + 1, datatype=XSD.integer)))
    conforma, texto, _ = validar_llc(g)
    assert not conforma and "ΣP ≠ K" in texto
    g = copy.deepcopy(abox)
    r1 = next(iter(g.subjects(predicate=MOACV.numeroRegion,
                              object=Literal(1, datatype=XSD.integer))))
    g.set((r1, MOACV.valor, Literal(json.dumps({"si": {"origen": "SY"}}))))
    conforma, texto, _ = validar_llc(g)
    assert not conforma and "DE-4" in texto


def test_sparql_decision_genealogia_roles_y_equidad(equipo, abox):
    ce = equipo.casos[-1]
    filas = Q.teorias_de_decision(abox, ce.trace_id)
    assert {f["rol"] for f in filas} == set(ROLES)
    t = equipo.agentes["matcher"].theories.theories[0]
    gen = Q.genealogia(abox, theory_iri(equipo.agentes["matcher"].name, t,
                                        equipo.agentes["matcher"].theories.q))
    assert gen["filas"][0]["n"] is not None and gen["filas"][0]["region"].endswith("/R5")
    por_rol = Q.favorable_por_rol_y_grupo(abox)
    assert {f["rol"] for f in por_rol} == set(ROLES)
    for r in ("parser", "matcher", "explainer"):
        assert sum(f["n"] for f in por_rol if f["rol"] == r) == equipo.motores[r].ciclo
    estados = Q.teorias_por_rol_y_estado(abox)
    assert sum(f["teorias"] for f in estados) == sum(len(equipo.agentes[r].theories)
                                                     for r in ROLES)


def test_abox_con_procedencia_de_compartir():
    cfg = cargar_config()
    c = ConfigCiclo.desde_yaml(cfg)
    casos = entorno.generar_escenario("BIO", 40, cfg["semilla"])
    motores = []
    for nombre in ("D", "R"):
        m = MotorLLC(AgenteLLC(nombre, "matcher"), RolMatcherLLC(0.1, cfg["semilla"]),
                     FairnessMonitor(tau=0.8, disparity_threshold=0.075), c)
        for caso in casos[:20 if nombre == "R" else 40]:
            m.paso(caso)
        motores.append(m)
    d, r = motores
    d.agente._estado = MaturityState.MATURE         # solo en el test; las demos ganan estados
    decs = {x.agente.name: [{"origin_group": y["grupo"], "decision": y["accion"]}
                            for y in x.ciclos] for x in motores}
    res = compartir("colaboracion", d.agente, r.agente, FairnessMonitor(disparity_threshold=0.075),
                    decs, 0, 0.05, r.es_acierto, a9="decisiones")
    assert res["aceptada"]
    prov = procedencia_compartida("R", "D", r.agente.theories.theories,
                                  d.agente.theories.theories)
    g = abox_equipo([("matcher", r.agente, r)], procedencia=prov)
    derivadas = list(g.subjects(predicate=PROV.wasDerivedFrom))
    assert derivadas and all((x, MOACV.rol, Literal("matcher")) in g for x in derivadas)
    assert (ciclo_iri("R", 1), MOACV.numeroCiclo, Literal(1, datatype=XSD.integer)) in g
