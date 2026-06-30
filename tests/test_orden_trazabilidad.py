"""
Ítem A (Becerra) — orden de ejecución en el triple store.

Los grafos RDF son conjuntos de tripletas: no preservan el orden de inserción, y al
serializar→recuperar ese orden se pierde. Estos tests corroboran que la trazabilidad
SECUENCIAL de decisiones sobrevive a un round-trip de serialización, anclada a un ordinal
explícito (`moacv:ordenEjecucion`) y recuperada con `ORDER BY`, sin depender del timestamp
(que puede colisionar) ni del orden de las tripletas.
"""
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF, XSD

from moav_hr.core.ontology import abox, queries
from moav_hr.instances.hr.pipeline import HRPipeline
from moav_hr.instances.hr.synthetic import get

MOACV = Namespace("https://moav-hr.diit.unlam.edu.ar/ontology/")


def _state():
    p = HRPipeline(mode="sim")
    p.warmup([get(3)])
    return p.process(get(3)), list(p.agents)


def test_orden_sobrevive_round_trip_serializacion():
    """ABox → Turtle → parsear de nuevo → SPARQL ORDER BY ?orden recupera la secuencia."""
    st, agents = _state()
    orden_original = [ev.action for ev in st["trail"].events]

    # round-trip: serializar a Turtle y parsear en un grafo NUEVO (se pierde el orden de triples)
    turtle = abox.build_abox(st, agents).serialize(format="turtle")
    g2 = Graph().parse(data=turtle, format="turtle")

    rec = queries.run(g2, queries.Q_EVENTS_ORDERED)
    orden_recuperado = [r["tipo"] for r in rec]

    assert orden_recuperado == orden_original, (orden_original, orden_recuperado)
    # los ordinales recuperados son 0..n-1, estrictamente crecientes
    ordinales = [int(r["orden"]) for r in rec]
    assert ordinales == list(range(len(orden_original)))


def test_ordinal_es_robusto_aunque_colisionen_timestamps():
    """
    Donde el timestamp falla (dos eventos con el mismo valor → desempate no garantizado por
    SPARQL), el ordinal explícito recupera el orden correcto tras el round-trip.
    """
    g = Graph()
    # A, B, C en ese orden; B y C comparten timestamp (colisión posible en sim, que corre rápido)
    for i, (name, ts) in enumerate([("A", 100.0), ("B", 100.5), ("C", 100.5)]):
        e = MOACV[f"Evento/{name}"]
        g.add((e, RDF.type, MOACV.EventoDecision))
        g.add((e, MOACV.timestamp, Literal(ts, datatype=XSD.double)))
        g.add((e, MOACV.ordenEjecucion, Literal(i, datatype=XSD.integer)))
        g.add((e, MOACV.tipo, Literal(name)))

    g2 = Graph().parse(data=g.serialize(format="turtle"), format="turtle")
    rec = [r["tipo"] for r in queries.run(g2, queries.Q_EVENTS_ORDERED)]
    assert rec == ["A", "B", "C"], rec
