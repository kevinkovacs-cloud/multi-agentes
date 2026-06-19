"""
Consultas SPARQL de ejemplo sobre el grafo de procedencia (v13 §2.5 / Eje 3).

Verifican la interoperabilidad: el audit trail, una vez RDF, es consultable. Incluye la
consulta de auditoría de sesgo «¿qué decisiones fueron influidas por el atributo X?».
"""
from __future__ import annotations
from rdflib import Graph

# decisiones y la teoría de la que derivan (procedencia PROV-O)
Q_DECISIONS_PROVENANCE = """
PREFIX moacv: <https://moav-hr.diit.unlam.edu.ar/ontology/>
PREFIX prov:  <http://www.w3.org/ns/prov#>
SELECT ?decision ?resultado (COUNT(?teoria) AS ?nTeorias)
WHERE {
  ?decision a moacv:Decision ; moacv:resultado ?resultado .
  OPTIONAL { ?decision prov:wasDerivedFrom ?teoria . }
} GROUP BY ?decision ?resultado
"""

# auditoría de sesgo: decisiones que usaron a un candidato con un atributo protegido dado
Q_DECISIONS_BY_ATTR = """
PREFIX moacv: <https://moav-hr.diit.unlam.edu.ar/ontology/>
PREFIX prov:  <http://www.w3.org/ns/prov#>
SELECT ?decision ?resultado ?origen
WHERE {
  ?decision a moacv:Decision ; moacv:resultado ?resultado ; prov:used ?cand .
  ?cand a moacv:Candidato ; moacv:origen ?origen .
}
"""

# escalamientos a revisión humana registrados (EU AI Act Art.14)
Q_ESCALATIONS = """
PREFIX moacv: <https://moav-hr.diit.unlam.edu.ar/ontology/>
SELECT (COUNT(?e) AS ?escalamientos)
WHERE { ?e a moacv:EventoEscalamiento . }
"""


def run(graph: Graph, query: str) -> list[dict]:
    rows = []
    for row in graph.query(query):
        rows.append({str(k): str(v) for k, v in zip(row.labels, row)})
    return rows
