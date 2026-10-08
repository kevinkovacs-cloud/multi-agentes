"""
Consultas SPARQL sobre la ABox del modo LLC — bloque E · E4 (sección 8 del handoff).

  1. Genealogía de una teoría: el ciclo en que nació (capa, estado del agente, caso,
     región 5), los ciclos que la reforzaron y, si vino de compartir, la teoría de la que
     deriva.
  2. Qué teorías de qué roles intervinieron en la decisión X (fueron plan en los ciclos de
     los roles que procesaron el caso).
  3. Teorías por rol y por estado del agente al nacer la teoría.
  4. Resultado favorable por rol y grupo (plano de auditoría): la base de e_rol.
"""
from __future__ import annotations
from decimal import Decimal
from typing import Optional

from rdflib import Graph, Literal, URIRef

_PRE = """PREFIX moacv: <https://moav-hr.diit.unlam.edu.ar/ontology/>
PREFIX prov:  <http://www.w3.org/ns/prov#>
"""

Q_GENEALOGIA = _PRE + """
SELECT ?agente ?rol ?clave ?p ?k ?u ?ciclo ?n ?capa ?estado ?caso ?region ?donante
       (COUNT(DISTINCT ?ref) AS ?refuerzos)
WHERE {
  ?teoria a moacv:Teoria ; moacv:deAgente ?ag ; moacv:rol ?rol ; moacv:clave ?clave ;
          moacv:P ?p ; moacv:K ?k ; moacv:U ?u .
  BIND (STR(?ag) AS ?agente)
  OPTIONAL { ?teoria prov:wasGeneratedBy ?ciclo .
             ?ciclo moacv:numeroCiclo ?n ; moacv:capa ?capa ; moacv:estadoAgente ?estado ;
                    moacv:caso ?caso . }
  OPTIONAL { ?teoria moacv:registradaEnRegion ?region . }
  OPTIONAL { ?teoria prov:wasDerivedFrom ?donante . }
  OPTIONAL { ?teoria moacv:reforzadaEn ?ref . }
}
GROUP BY ?agente ?rol ?clave ?p ?k ?u ?ciclo ?n ?capa ?estado ?caso ?region ?donante
"""

Q_REFUERZOS = _PRE + """
SELECT ?n ?capa ?estado WHERE {
  ?teoria moacv:reforzadaEn ?ciclo .
  ?ciclo moacv:numeroCiclo ?n ; moacv:capa ?capa ; moacv:estadoAgente ?estado .
} ORDER BY ?n
"""

Q_TEORIAS_DE_DECISION = _PRE + """
SELECT ?rol ?n ?capa ?estado ?accion ?motivo ?clave ?p ?k ?u WHERE {
  ?decision a moacv:Decision ; moacv:traceId ?traza ; prov:wasInformedBy ?ciclo .
  ?ciclo prov:wasAssociatedWith ?ag ; moacv:numeroCiclo ?n ; moacv:capa ?capa ;
         moacv:estadoAgente ?estado ; moacv:accion ?accion ; moacv:motivo ?motivo .
  ?ag moacv:rol ?rol .
  OPTIONAL { ?ciclo moacv:usaTeoria ?t . ?t moacv:clave ?clave ; moacv:P ?p ; moacv:K ?k ;
             moacv:U ?u . }
} ORDER BY ?rol
"""

Q_TEORIAS_POR_ROL_Y_ESTADO = _PRE + """
SELECT ?rol ?estado (COUNT(?t) AS ?teorias) (SUM(?p) AS ?sumaP)
       (SUM(IF(?u > 0.75, 1, 0)) AS ?exitosas)
WHERE {
  ?t a moacv:Teoria ; moacv:rol ?rol ; moacv:estadoAlNacer ?estado ; moacv:P ?p ; moacv:U ?u .
} GROUP BY ?rol ?estado ORDER BY ?rol ?estado
"""

Q_FAVORABLE_POR_ROL_Y_GRUPO = _PRE + """
SELECT ?rol ?grupo (COUNT(?l) AS ?n) (SUM(IF(?fav, 1, 0)) AS ?favorables)
WHERE {
  ?l a moacv:LecturaEquidad ; moacv:grupoAuditoria ?grupo ; moacv:favorable ?fav ;
     moacv:deCiclo ?ciclo .
  ?ciclo prov:wasAssociatedWith ?ag .
  ?ag moacv:rol ?rol .
} GROUP BY ?rol ?grupo ORDER BY ?rol ?grupo
"""


def _filas(res) -> list[dict]:
    out = []
    for fila in res:
        d = {}
        for k, v in fila.asdict().items():
            x = v.toPython() if isinstance(v, Literal) else str(v)
            d[k] = float(x) if isinstance(x, Decimal) else x
        out.append(d)
    return out


def genealogia(g: Graph, teoria: URIRef) -> dict:
    base = _filas(g.query(Q_GENEALOGIA, initBindings={"teoria": teoria}))
    refuerzos = _filas(g.query(Q_REFUERZOS, initBindings={"teoria": teoria}))
    return {"teoria": str(teoria), "filas": base, "refuerzos": refuerzos}


def teorias_de_decision(g: Graph, trace_id: str) -> list[dict]:
    return _filas(g.query(Q_TEORIAS_DE_DECISION, initBindings={"traza": Literal(trace_id)}))


def teorias_por_rol_y_estado(g: Graph) -> list[dict]:
    return _filas(g.query(Q_TEORIAS_POR_ROL_Y_ESTADO))


def favorable_por_rol_y_grupo(g: Graph, roles: Optional[list[str]] = None) -> list[dict]:
    filas = _filas(g.query(Q_FAVORABLE_POR_ROL_Y_GRUPO))
    return [f for f in filas if roles is None or f["rol"] in roles]


def brecha_por_rol(filas: list[dict]) -> dict[str, dict]:
    """Brecha de la tasa favorable entre los dos grupos, por rol (a partir de la consulta 4)."""
    por_rol: dict[str, dict] = {}
    for f in filas:
        por_rol.setdefault(f["rol"], {})[f["grupo"]] = f["favorables"] / f["n"]
    return {r: {"tasas": t, "brecha": round(abs(max(t.values()) - min(t.values())), 4)
                if len(t) == 2 else None} for r, t in por_rol.items()}
