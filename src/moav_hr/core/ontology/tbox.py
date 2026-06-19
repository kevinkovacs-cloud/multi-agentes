"""
TBox — esquema de la ontología (v13 §2.5). Clases, jerarquías, propiedades y axiomas,
con alineación a PROV-O. Se cura/valida una sola vez (es el esquema, no las instancias).
"""
from __future__ import annotations
from rdflib import Graph, Literal
from rdflib.namespace import RDF, RDFS, OWL, XSD

from moav_hr.core.ontology.ns import MOACV, PROV

CLASSES = [
    "Agente", "AgenteAuditor", "Teoria", "Situacion", "SituacionInicial", "SituacionFinal",
    "Accion", "BaseDeConocimiento", "Decision", "VentanaDeDecisiones", "EventoDeAuditoria",
    "EventoDecision", "EventoEscalamiento", "EventoTransferencia", "EventoBloqueoPorEquidad",
    "Candidato", "AtributoProtegido",
]

SUBCLASSES = [
    ("AgenteAuditor", "Agente"), ("SituacionInicial", "Situacion"),
    ("SituacionFinal", "Situacion"), ("EventoDecision", "EventoDeAuditoria"),
    ("EventoEscalamiento", "EventoDeAuditoria"), ("EventoTransferencia", "EventoDeAuditoria"),
    ("EventoBloqueoPorEquidad", "EventoDeAuditoria"),
]

# alineación PROV-O (capa de procedencia)
PROV_ALIGN = [
    ("Agente", PROV.Agent), ("Decision", PROV.Activity),
    ("EventoDeAuditoria", PROV.Activity), ("Teoria", PROV.Entity),
]

OBJECT_PROPS = {
    "poseeBase": ("Agente", "BaseDeConocimiento"),
    "contieneTeoria": ("BaseDeConocimiento", "Teoria"),
    "registra": ("Agente", "Teoria"),
    "aplicaEn": ("Teoria", "Situacion"),
    "esIgualA": ("Teoria", "Teoria"),
    "esSimilarA": ("Teoria", "Teoria"),
    "cooperaCon": ("Agente", "Agente"),
    "colaboraCon": ("Agente", "Agente"),
    "produce": ("Agente", "Decision"),
    "audita": ("AgenteAuditor", "Decision"),
    "ponderaComparticion": ("AgenteAuditor", "EventoTransferencia"),
    "generaEvento": ("Agente", "EventoDeAuditoria"),
}

DATA_PROPS = {
    "estado": XSD.string, "capa": XSD.string, "P": XSD.integer, "K": XSD.integer,
    "U": XSD.double, "confiabilidad": XSD.double, "reputacionEquidad": XSD.double,
    "umbralEquidad": XSD.double, "umbralDiversidad": XSD.double, "fairW": XSD.double,
    "accW": XSD.double, "timestamp": XSD.double, "scoreMatching": XSD.double,
    "resultado": XSD.string, "criterioEquidad": XSD.string, "genero": XSD.string,
    "origen": XSD.string, "edad": XSD.integer, "representacionJSON": XSD.string, "tipo": XSD.string,
}


def build_tbox() -> Graph:
    g = Graph()
    g.bind("moacv", MOACV)
    g.bind("prov", PROV)
    g.bind("owl", OWL)
    for c in CLASSES:
        g.add((MOACV[c], RDF.type, OWL.Class))
    for sub, sup in SUBCLASSES:
        g.add((MOACV[sub], RDFS.subClassOf, MOACV[sup]))
    for cls, prov_cls in PROV_ALIGN:
        g.add((MOACV[cls], RDFS.subClassOf, prov_cls))
    for p, (dom, rng) in OBJECT_PROPS.items():
        g.add((MOACV[p], RDF.type, OWL.ObjectProperty))
        g.add((MOACV[p], RDFS.domain, MOACV[dom]))
        g.add((MOACV[p], RDFS.range, MOACV[rng]))
    g.add((MOACV.cooperaCon, RDF.type, OWL.SymmetricProperty))   # Def. 7 (simétrica)
    for p, rng in DATA_PROPS.items():
        g.add((MOACV[p], RDF.type, OWL.DatatypeProperty))
        g.add((MOACV[p], RDFS.range, rng))
    # axioma documentado: orden total de evolución (para lectura humana)
    g.add((MOACV.ordenEvolucion, RDF.type, RDFS.Literal))
    g.add((MOACV.ordenEvolucion, RDFS.comment,
           Literal("Born ≺ Novato ≺ Trained ≺ Mature (orden total)")))
    return g


def tbox_turtle() -> str:
    return build_tbox().serialize(format="turtle")
