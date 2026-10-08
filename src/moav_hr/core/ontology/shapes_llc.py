"""
Shapes SHACL del modo LLC — bloque E · E4. Se suman a las de `shapes.py` (que no cambian).

  · TeoriaLLCShape: cada teoría tiene rol, agente, celda (Si, A) y al menos una actividad que
    la generó (`prov:wasGeneratedBy`: el ciclo en que nació y, si además llegó por compartir,
    la actividad de compartir de `sharing_rdf.procedencia_compartida`); y en su celda vale el
    invariante ΣP = K del registro de la Fig. 4.13 (Ierache 2010, p. 113), como restricción
    SPARQL.
  · CicloLLCShape: número, capa, estado ganado del agente, agente asociado y siete regiones.
  · RegionLLCShape: número de región 1 a 7, nombre, valor y ciclo.
  · SituacionInicialSinAtributoShape (DE-4): el valor de la región 1 no tiene claves de
    atributos protegidos.
  · DecisionLLCShape y LecturaEquidadShape.
"""
from __future__ import annotations
from rdflib import Graph

from moav_hr.core.ontology.shapes import SHAPES_TTL

SHAPES_LLC_TTL = """
@prefix sh:    <http://www.w3.org/ns/shacl#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
@prefix owl:   <http://www.w3.org/2002/07/owl#> .
@prefix prov:  <http://www.w3.org/ns/prov#> .
@prefix moacv: <https://moav-hr.diit.unlam.edu.ar/ontology/> .

moacv:prefijosLLC a owl:Ontology ;
    sh:declare [ sh:prefix "moacv" ; sh:namespace "https://moav-hr.diit.unlam.edu.ar/ontology/"^^xsd:anyURI ] ,
               [ sh:prefix "prov" ; sh:namespace "http://www.w3.org/ns/prov#"^^xsd:anyURI ] .

moacv:TeoriaLLCShape a sh:NodeShape ;
    sh:targetClass moacv:Teoria ;
    sh:property [ sh:path moacv:rol ; sh:minCount 1 ; sh:maxCount 1 ] ;
    sh:property [ sh:path moacv:deAgente ; sh:minCount 1 ; sh:maxCount 1 ; sh:class moacv:Agente ] ;
    sh:property [ sh:path moacv:celda ; sh:minCount 1 ; sh:maxCount 1 ] ;
    sh:property [ sh:path prov:wasGeneratedBy ; sh:minCount 1 ; sh:class prov:Activity ] ;
    sh:sparql [
        a sh:SPARQLConstraint ;
        sh:message "ΣP ≠ K en la celda (Si, A) del agente (registro de la Fig. 4.13, Ierache 2010, p. 113)" ;
        sh:prefixes moacv:prefijosLLC ;
        sh:select \"\"\"
            SELECT $this ?value WHERE {
                $this moacv:K ?k .
                { SELECT $this (SUM(?p) AS ?sp) WHERE {
                      $this moacv:celda ?c ; moacv:deAgente ?ag .
                      ?t a moacv:Teoria ; moacv:celda ?c ; moacv:deAgente ?ag ; moacv:P ?p .
                  } GROUP BY $this }
                FILTER (?sp != ?k)
                BIND (?sp AS ?value)
            }\"\"\" ] .

moacv:CicloLLCShape a sh:NodeShape ;
    sh:targetClass moacv:CicloLLC ;
    sh:property [ sh:path moacv:numeroCiclo ; sh:datatype xsd:integer ; sh:minCount 1 ;
                  sh:maxCount 1 ; sh:minInclusive 1 ] ;
    sh:property [ sh:path moacv:capa ; sh:minCount 1 ; sh:in ( "BIO" "TBO" "WIO" ) ] ;
    sh:property [ sh:path moacv:estadoAgente ; sh:minCount 1 ;
                  sh:in ( "Born" "Novice" "Trained" "Mature" ) ] ;
    sh:property [ sh:path prov:wasAssociatedWith ; sh:minCount 1 ; sh:class moacv:Agente ] ;
    sh:property [ sh:path moacv:tieneRegion ; sh:minCount 7 ; sh:maxCount 7 ;
                  sh:class moacv:RegionLLC ] .

moacv:RegionLLCShape a sh:NodeShape ;
    sh:targetClass moacv:RegionLLC ;
    sh:property [ sh:path moacv:numeroRegion ; sh:datatype xsd:integer ; sh:minCount 1 ;
                  sh:maxCount 1 ; sh:minInclusive 1 ; sh:maxInclusive 7 ] ;
    sh:property [ sh:path moacv:valor ; sh:minCount 1 ; sh:maxCount 1 ] ;
    sh:property [ sh:path moacv:enCiclo ; sh:minCount 1 ; sh:maxCount 1 ;
                  sh:class moacv:CicloLLC ] .

moacv:SituacionInicialSinAtributoShape a sh:NodeShape ;
    sh:targetClass moacv:SituacionInicialLLC ;
    sh:property [ sh:path moacv:valor ;
                  sh:not [ sh:pattern "\\"(origin|origin_group|origen|nacionalidad|gender|genero|género|sexo|age|edad)\\"\\\\s*:" ;
                           sh:flags "i" ] ;
                  sh:message "atributo protegido en la situación inicial (DE-4)" ] .

moacv:DecisionLLCShape a sh:NodeShape ;
    sh:targetClass moacv:Decision ;
    sh:property [ sh:path moacv:resultado ; sh:minCount 1 ;
                  sh:in ( "ADVANCE" "REJECT" "ESCALATE_HUMAN" ) ] .

moacv:LecturaEquidadShape a sh:NodeShape ;
    sh:targetClass moacv:LecturaEquidad ;
    sh:property [ sh:path moacv:grupoAuditoria ; sh:minCount 1 ; sh:maxCount 1 ] ;
    sh:property [ sh:path moacv:favorable ; sh:datatype xsd:boolean ; sh:minCount 1 ;
                  sh:maxCount 1 ] ;
    sh:property [ sh:path moacv:deCiclo ; sh:minCount 1 ; sh:class moacv:CicloLLC ] .
"""


def shapes_llc_graph() -> Graph:
    """Shapes de `shapes.py` más las del modo LLC."""
    g = Graph().parse(data=SHAPES_TTL, format="turtle")
    return g.parse(data=SHAPES_LLC_TTL, format="turtle")


def validar_llc(data_graph: Graph) -> tuple[bool, str, Graph]:
    """Valida la ABox del equipo. Devuelve (conforma, reporte, grafo de resultados)."""
    from pyshacl import validate as _validate
    conforma, resultados, texto = _validate(data_graph, shacl_graph=shapes_llc_graph(),
                                            inference="none", abort_on_first=False,
                                            advanced=True)
    return bool(conforma), texto, resultados
