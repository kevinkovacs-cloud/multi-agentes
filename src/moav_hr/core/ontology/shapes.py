"""
SHACL shapes + validación (v13 §2.5 / Eje 3 — "corroborar la correcta generación RDF").

Corrobora la conformidad del ABox respecto del esquema: P ≤ K, U y reputación en [0,1],
estado en el dominio permitido. `validate()` corre pySHACL y devuelve (conforms, texto).
"""
from __future__ import annotations
from rdflib import Graph

from moav_hr.core.ontology.tbox import build_tbox

SHAPES_TTL = """
@prefix sh:    <http://www.w3.org/ns/shacl#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
@prefix moacv: <https://moav-hr.diit.unlam.edu.ar/ontology/> .

moacv:TeoriaShape a sh:NodeShape ;
    sh:targetClass moacv:Teoria ;
    sh:property [ sh:path moacv:P ; sh:datatype xsd:integer ; sh:minInclusive 0 ;
                  sh:lessThanOrEquals moacv:K ] ;       # invariante P ≤ K (Def. 3)
    sh:property [ sh:path moacv:K ; sh:datatype xsd:integer ; sh:minInclusive 0 ] ;
    sh:property [ sh:path moacv:U ; sh:minInclusive 0 ; sh:maxInclusive 1 ] ;
    sh:property [ sh:path moacv:confiabilidad ; sh:minInclusive 0 ; sh:maxInclusive 1 ] .

moacv:AgenteShape a sh:NodeShape ;
    sh:targetClass moacv:Agente ;
    sh:property [ sh:path moacv:estado ;
                  sh:in ( "born" "novato" "trained" "mature" ) ] ;
    sh:property [ sh:path moacv:reputacionEquidad ; sh:minInclusive 0 ; sh:maxInclusive 1 ] .
"""


def shapes_graph() -> Graph:
    return Graph().parse(data=SHAPES_TTL, format="turtle")


def validate(data_graph: Graph) -> tuple[bool, str]:
    """Valida el ABox contra las shapes SHACL. Devuelve (conforms, reporte)."""
    from pyshacl import validate as _validate
    conforms, _results_graph, results_text = _validate(
        data_graph,
        shacl_graph=shapes_graph(),
        ont_graph=build_tbox(),
        inference="none",
        abort_on_first=False,
    )
    return conforms, results_text
