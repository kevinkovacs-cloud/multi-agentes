"""
ABox del modo LLC — bloque E · E4 (punto 4: la traza completa de un equipo en RDF).

Extiende la ABox de `abox.py` sin cambiarla. Por cada agente del equipo materializa:

  · cada ciclo percepción–acción como `moacv:CicloLLC` (prov:Activity) asociado al agente,
    con capa, estado del agente, acción, motivo del planificador y la teoría usada como plan;
  · siete nodos `moacv:RegionLLC` por ciclo (regiones 1 a 7 del LLC, Ierache 2010, §4.2,
    pp. 61–64) con sus valores en JSON;
  · cada teoría ⟨Si, A, Sf, P, K, U⟩ con su rol, su agente, su celda (Si, A) y
    `prov:wasGeneratedBy` el ciclo en que nació (registrada en la región 5); los ciclos que
    la reforzaron (`moacv:reforzadaEn`) y, si vino de compartir, `prov:wasDerivedFrom` la
    teoría del donante (grafo de `sharing_rdf.procedencia_compartida`);
  · cada decisión final como `moacv:Decision`, informada por los ciclos de los roles que
    procesaron el caso y derivada de las teorías que fueron plan en esos ciclos;
  · las lecturas de equidad del plano de auditoría (`moacv:LecturaEquidad`: grupo y si el
    resultado del rol fue favorable). El atributo protegido vive solo ahí (DE-4).

Genérico: recibe agentes y motores del core; no importa `instances/`.
"""
from __future__ import annotations
import json
from decimal import Decimal
from typing import Iterable, Optional
from urllib.parse import quote

from rdflib import Graph, Literal
from rdflib.namespace import RDF, XSD

from moav_hr.core.ontology.abox import _agent_node, theory_clave, theory_iri
from moav_hr.core.ontology.ns import MOACV, PROV
from moav_hr.core.theory import q_canonical, theory_key

NOMBRE_REGION = {1: "situación inicial", 2: "acción", 3: "situación final", 4: "utilidad",
                 5: "aprendizaje", 6: "estadísticas", 7: "evolución"}


# estadísticas de la región 6 que se materializan (§4.4.9); la instantánea completa queda en
# el JSON del motor
ESTADISTICAS_R6 = ("ciclos", "ciclos_exitosos", "teorias_acumuladas", "teorias_nuevas",
                   "teorias_exitosas", "planes", "planes_exitosos", "azares")


def _json(x) -> str:
    return json.dumps(x, ensure_ascii=False, sort_keys=True, default=str)


def ciclo_iri(agente: str, n: int):
    return MOACV[f"Ciclo/{quote(agente, safe='')}/{n:04d}"]


def celda_teoria(t, q) -> str:
    """Celda (Si, A) de la teoría: donde vale ΣP = K (Fig. 4.13; p. 113)."""
    k = theory_key(t, q)
    return json.dumps([k[0], k[1]], ensure_ascii=False)


def valores_region(reg: dict) -> dict[int, dict]:
    """Valores de las siete regiones de un ciclo, a partir del registro del motor."""
    return {
        1: {"si": reg["si"], "caso": reg["caso"]},
        2: {"accion": reg["accion"], "motivo": reg["motivo"], "es_azar": reg["es_azar"],
            "teoria_plan": reg["teoria_plan"], "accion_bio": reg["accion_bio"],
            "candidatas": [{"id": c["id"], "a": c["a"], "sf": c["sf"], "u": round(c["u_tarea"], 4),
                            "p": c["p"], "k": c["k"]} for c in reg["candidatas"]]},
        3: {"sf": reg["sf"], "fuente": reg["fuente_sf"]},
        4: {"u_tarea": reg["u_tarea"]},
        5: {"registro": reg["registro"], "teoria": reg["teoria_registrada"], "p": reg["p"],
            "k": reg["k"], "u": round(reg["u"], 6)},
        6: {"exitoso": reg["exitoso"], **{k: reg["estadisticas"][k] for k in ESTADISTICAS_R6}},
        7: (reg.get("evolucion") if reg.get("evolucion") is not None
            else {"evaluada": False, "sin_r7": reg.get("sin_r7")}),
    }


def _nacimientos(motor) -> dict[int, dict]:
    """id de teoría → ciclo en que se registró por primera vez (nueva o similar)."""
    out: dict[int, dict] = {}
    for reg in motor.ciclos:
        if reg["registro"] in ("nueva", "similar") and reg["teoria_registrada"] not in out:
            out[reg["teoria_registrada"]] = reg
    return out


def abox_equipo(miembros: Iterable[tuple[str, object, object]], decisiones: Iterable[dict] = (),
                procedencia: Optional[Graph] = None, regiones: bool = True) -> Graph:
    """
    miembros: (rol, agente, motor) de cada rol con teorías del equipo.
    decisiones: {"trace_id", "resultado", "ciclos": {rol: número de ciclo del rol}}.
    procedencia: grafo de `procedencia_compartida` si hubo compartición (E3/E5).
    """
    g = Graph()
    g.bind("moacv", MOACV)
    g.bind("prov", PROV)
    ag_de_rol: dict[str, str] = {}
    usa: dict = {}                                   # ciclo IRI → teoría IRI usada como plan
    for rol, agente, motor in miembros:
        nombre = agente.name
        ag_de_rol[rol] = nombre
        q = getattr(agente.theories, "q", q_canonical)
        au = _agent_node(g, nombre)
        g.add((au, MOACV.rol, Literal(rol)))
        g.add((au, MOACV.estado, Literal(agente.maturity.label)))
        g.add((au, MOACV.capa, Literal(agente.layer.value)))
        por_id = {t.id: t for t in agente.theories.theories}
        for reg in motor.ciclos:
            cu = ciclo_iri(nombre, reg["ciclo"])
            g.add((cu, RDF.type, MOACV.CicloLLC))
            g.add((cu, RDF.type, PROV.Activity))
            g.add((cu, PROV.wasAssociatedWith, au))
            g.add((cu, MOACV.numeroCiclo, Literal(int(reg["ciclo"]), datatype=XSD.integer)))
            g.add((cu, MOACV.capa, Literal(reg["capa"])))
            g.add((cu, MOACV.estadoAgente, Literal(reg["estado"])))
            g.add((cu, MOACV.accion, Literal(reg["accion"])))
            g.add((cu, MOACV.motivo, Literal(reg["motivo"])))
            g.add((cu, MOACV.uTarea, Literal(float(reg["u_tarea"]), datatype=XSD.double)))
            g.add((cu, MOACV.registro, Literal(reg["registro"])))
            g.add((cu, MOACV.caso, Literal(_json(reg["caso"]))))
            plan = por_id.get(reg["teoria_plan"]) if reg["teoria_plan"] is not None else None
            if plan is not None:
                tu = theory_iri(nombre, plan, q)
                g.add((cu, MOACV.usaTeoria, tu))
                usa[cu] = tu
            if regiones:
                for k, valor in valores_region(reg).items():
                    ru = MOACV[f"Ciclo/{quote(nombre, safe='')}/{reg['ciclo']:04d}/R{k}"]
                    g.add((ru, RDF.type, MOACV.RegionLLC))
                    if k == 1:
                        g.add((ru, RDF.type, MOACV.SituacionInicialLLC))
                    g.add((ru, MOACV.numeroRegion, Literal(k, datatype=XSD.integer)))
                    g.add((ru, MOACV.nombreRegion, Literal(NOMBRE_REGION[k])))
                    g.add((ru, MOACV.valor, Literal(_json(valor))))
                    g.add((ru, MOACV.enCiclo, cu))
                    g.add((cu, MOACV.tieneRegion, ru))
            for i, (grupo, favorable) in enumerate(reg.get("equidad") or []):
                lu = MOACV[f"Ciclo/{quote(nombre, safe='')}/{reg['ciclo']:04d}/E{i + 1:02d}"]
                g.add((lu, RDF.type, MOACV.LecturaEquidad))
                g.add((lu, MOACV.deCiclo, cu))
                g.add((lu, MOACV.plano, Literal("auditoria")))
                g.add((lu, MOACV.grupoAuditoria, Literal(grupo)))
                g.add((lu, MOACV.favorable, Literal(bool(favorable), datatype=XSD.boolean)))
            if reg["registro"] == "igual" and reg["teoria_registrada"] in por_id:
                g.add((theory_iri(nombre, por_id[reg["teoria_registrada"]], q),
                       MOACV.reforzadaEn, cu))
        nac = _nacimientos(motor)
        base = MOACV[f"Base/{quote(nombre, safe='')}"]
        g.add((base, RDF.type, MOACV.BaseDeConocimiento))
        g.add((au, MOACV.poseeBase, base))
        for t in agente.theories.theories:
            tu = theory_iri(nombre, t, q)
            g.add((tu, RDF.type, MOACV.Teoria))
            g.add((tu, RDF.type, PROV.Entity))
            g.add((base, MOACV.contieneTeoria, tu))
            g.add((tu, MOACV.deAgente, au))
            g.add((tu, MOACV.rol, Literal(rol)))
            g.add((tu, MOACV.clave, Literal(theory_clave(t, q))))
            g.add((tu, MOACV.celda, Literal(celda_teoria(t, q))))
            g.add((tu, MOACV.accion, Literal(t.a)))
            g.add((tu, MOACV.P, Literal(int(t.p), datatype=XSD.integer)))
            g.add((tu, MOACV.K, Literal(int(t.k), datatype=XSD.integer)))
            g.add((tu, MOACV.U, Literal(Decimal(repr(float(t.u))), datatype=XSD.decimal)))
            g.add((tu, MOACV.situacionInicial, Literal(_json(t.si))))
            g.add((tu, MOACV.situacionFinal, Literal(_json(t.sf))))
            reg = nac.get(t.id)
            if reg is not None:
                cu = ciclo_iri(nombre, reg["ciclo"])
                g.add((tu, PROV.wasGeneratedBy, cu))
                g.add((tu, MOACV.capaDeNacimiento, Literal(reg["capa"])))
                g.add((tu, MOACV.estadoAlNacer, Literal(reg["estado"])))
                if regiones:
                    g.add((tu, MOACV.registradaEnRegion,
                           MOACV[f"Ciclo/{quote(nombre, safe='')}/{reg['ciclo']:04d}/R5"]))
    orq = _agent_node(g, "Orchestrator")
    g.add((orq, MOACV.rol, Literal("orchestrator")))
    g.add((orq, MOACV.sinTeorias, Literal("DE-7: infraestructura de la capa BIO")))
    for d in decisiones:
        du = MOACV[f"Decision/{quote(d['trace_id'], safe='')}"]
        g.add((du, RDF.type, MOACV.Decision))
        g.add((du, RDF.type, PROV.Activity))
        g.add((du, MOACV.resultado, Literal(d["resultado"])))
        g.add((du, MOACV.traceId, Literal(d["trace_id"])))
        g.add((du, PROV.wasAssociatedWith, orq))
        for rol, n in d["ciclos"].items():
            if rol not in ag_de_rol:
                continue
            cu = ciclo_iri(ag_de_rol[rol], n)
            g.add((du, PROV.wasInformedBy, cu))
            if cu in usa:
                g.add((du, PROV.wasDerivedFrom, usa[cu]))
    if procedencia is not None:
        g += procedencia
    return g
