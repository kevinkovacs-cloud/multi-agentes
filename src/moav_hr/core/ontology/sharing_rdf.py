"""
Compartición de teorías entre agentes vía la ontología — máquina a máquina (M2M).

Obs. Becerra: el fuerte de la web semántica no es solo registrar eventos/decisiones para
auditoría, sino usar la ontología para **estructurar las teorías ⟨Si,A,Sf,P,K,U⟩ y
compartirlas entre agentes de forma estándar, independientemente del framework**.

Este módulo materializa ese intercambio: un agente exporta su base de teorías a RDF/Turtle
(`theories_to_turtle`) y otro agente la reconstruye **desde el RDF** (`theories_from_turtle`),
sin compartir objetos en memoria. El vocabulario es el de §2.5 (Teoria, BaseDeConocimiento,
SituacionInicial/Final, aplicaEn, P/K/U/accion), de modo que cualquier sistema que entienda
la ontología puede consumir las teorías.
"""
from __future__ import annotations
import json

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, XSD

from moav_hr.core.ontology.ns import MOACV
from moav_hr.core.theory import Theory, serialize


def theories_to_turtle(theories: list[Theory], agent: str = "AgenteEmisor") -> str:
    """Serializa una base de teorías a RDF/Turtle con el vocabulario de §2.5."""
    g = Graph()
    g.bind("moacv", MOACV)
    au = MOACV[f"Agente/{agent}"]
    base = MOACV[f"Base/{agent}"]
    g.add((au, RDF.type, MOACV.Agente))
    g.add((base, RDF.type, MOACV.BaseDeConocimiento))
    g.add((au, MOACV.poseeBase, base))
    for i, t in enumerate(theories):
        tu = MOACV[f"Teoria/{agent}-{i}"]
        g.add((tu, RDF.type, MOACV.Teoria))
        g.add((base, MOACV.contieneTeoria, tu))
        g.add((au, MOACV.registra, tu))
        g.add((tu, MOACV.P, Literal(int(t.p), datatype=XSD.integer)))
        g.add((tu, MOACV.K, Literal(int(t.k), datatype=XSD.integer)))
        g.add((tu, MOACV.U, Literal(round(float(t.u), 6), datatype=XSD.double)))
        g.add((tu, MOACV.accion, Literal(t.a)))
        si = MOACV[f"Si/{agent}-{i}"]
        g.add((si, RDF.type, MOACV.SituacionInicial))
        g.add((si, MOACV.representacionJSON, Literal(serialize(t.si))))
        g.add((tu, MOACV.aplicaEn, si))
        sf = MOACV[f"Sf/{agent}-{i}"]
        g.add((sf, RDF.type, MOACV.SituacionFinal))
        g.add((sf, MOACV.representacionJSON, Literal(serialize(t.sf))))
        g.add((tu, MOACV.aplicaEn, sf))
    return g.serialize(format="turtle")


_Q_THEORIES = """
PREFIX moacv: <https://moav-hr.diit.unlam.edu.ar/ontology/>
SELECT ?t ?p ?k ?u ?accion ?siJson ?sfJson
WHERE {
  ?t a moacv:Teoria ; moacv:P ?p ; moacv:K ?k ; moacv:U ?u .
  OPTIONAL { ?t moacv:accion ?accion }
  OPTIONAL { ?t moacv:aplicaEn ?si . ?si a moacv:SituacionInicial ; moacv:representacionJSON ?siJson }
  OPTIONAL { ?t moacv:aplicaEn ?sf . ?sf a moacv:SituacionFinal   ; moacv:representacionJSON ?sfJson }
}
"""


def theories_from_turtle(source: "Graph | str") -> list[Theory]:
    """
    Reconstruye las teorías ⟨Si,A,Sf,P,K,U⟩ **desde el RDF** (Turtle o Graph), sin acceder
    al objeto original. Acepta tanto la salida de `theories_to_turtle` como un ABox completo
    (`abox.build_abox`), porque comparten el vocabulario de §2.5.
    """
    g = source if isinstance(source, Graph) else Graph().parse(data=source, format="turtle")
    out: list[Theory] = []
    for row in g.query(_Q_THEORIES):
        si = json.loads(str(row.siJson)) if row.siJson is not None else {}
        sf = json.loads(str(row.sfJson)) if row.sfJson is not None else {}
        a = str(row.accion) if row.accion is not None else ""
        out.append(Theory(si=si, a=a, sf=sf,
                          p=int(row.p), k=int(row.k), u=float(row.u)))
    return out
