"""
Bloque C · C4 — U se exporta sin redondeo y se exportan los usos propios (k_own).

Antes abox redondeaba U a 4 decimales (y sharing_rdf a 6). Ahora el literal lleva la
precisión completa y se agrega la propiedad de datos `usos` = k_own (declarada en la
TBox con el mismo patrón que P y K). K se sigue exportando igual. Al importar, k_own se
reconstruye desde `usos` si está.

LÍMITE ENCONTRADO (pregunta para Claude chat, ver reporte): el serializador Turtle de
rdflib 7.6 escribe xsd:double abreviado con "%e" (7 cifras: 6.666667e-01), así que la
ida y vuelta EXACTA por Turtle que pide la especificación no se cumple con xsd:double.
Es exacta en el grafo, en N-Triples, JSON-LD y RDF/XML, y en Turtle con xsd:decimal.
El criterio literal de la especificación queda como xfail(strict=True): si se resuelve
(cambio de datatype o de formato, o rdflib deja de abreviar), el test avisa (XPASS).
"""
from types import SimpleNamespace

import pytest
from rdflib import Graph

from moav_hr.core.ontology import abox, shapes
from moav_hr.core.ontology.ns import MOACV
from moav_hr.core.ontology.sharing_rdf import theories_from_turtle, theories_to_turtle
from moav_hr.core.ontology.tbox import build_tbox
from moav_hr.core.theory import Theory, TheoryBase
from moav_hr.instances.hr.pipeline import HRPipeline
from moav_hr.instances.hr.synthetic import get

from rdflib.namespace import OWL, RDF


def _teoria():
    # tras una fusión: K expuesto (celda) = 10, usos propios = 4
    return Theory(si={"x": 1}, a="ADVANCE", sf={"r": "ok"}, p=3, k=10, u=2 / 3, k_own=4)


def _agent(base):
    return SimpleNamespace(name="Matcher", maturity=SimpleNamespace(label="Trained"),
                           layers="BIO+TBO", reputation=lambda: 0.9, theories=base)


@pytest.mark.xfail(strict=True, reason="rdflib 7.6: Turtle abrevia xsd:double a 7 cifras "
                                        "(%e) — decisión de datatype/formato pendiente (C4)")
def test_u_ida_y_vuelta_exacta_por_turtle():
    """Criterio literal de la especificación C4 (a)."""
    rec = theories_from_turtle(theories_to_turtle([_teoria()], agent="Matcher"))
    assert rec[0].u == 2 / 3


def test_u_sin_redondeo_en_el_grafo_y_en_ntriples():
    base = TheoryBase()
    base.add(_teoria())
    g = abox.build_abox({}, [_agent(base)])
    assert [float(o) for o in g.objects(None, MOACV.U)] == [2 / 3]          # en el grafo
    nt = g.serialize(format="nt")                                            # N-Triples
    assert [float(o) for o in Graph().parse(data=nt, format="nt").objects(None, MOACV.U)] == [2 / 3]


def test_u_por_turtle_mejora_respecto_del_redondeo_anterior():
    # antes: 4 decimales en abox (error ≈ 3.3e-5); ahora: 7 cifras de rdflib (≈ 3.3e-8)
    base = TheoryBase()
    base.add(_teoria())
    ttl = abox.build_abox({}, [_agent(base)]).serialize(format="turtle")
    u = [float(o) for o in Graph().parse(data=ttl, format="turtle").objects(None, MOACV.U)][0]
    assert abs(u - 2 / 3) < 1e-7
    rec = theories_from_turtle(theories_to_turtle([_teoria()], agent="Matcher"))
    assert abs(rec[0].u - 2 / 3) < 1e-7


def test_usos_existe_y_vale_k_own():
    g = Graph().parse(data=theories_to_turtle([_teoria()], agent="Matcher"), format="turtle")
    assert [int(o) for o in g.objects(None, MOACV.usos)] == [4]
    assert [int(o) for o in g.objects(None, MOACV.K)] == [10]      # K sin cambios
    base = TheoryBase()
    base.add(_teoria())
    ga = abox.build_abox({}, [_agent(base)])
    assert [int(o) for o in ga.objects(None, MOACV.usos)] == [4]
    # la importación reconstruye k_own desde `usos`
    t = theories_from_turtle(g)[0]
    assert (t.p, t.k, t.k_own) == (3, 10, 4)
    # declarada en la TBox como propiedad de datos
    assert (MOACV.usos, RDF.type, OWL.DatatypeProperty) in build_tbox()


def test_shacl_conforme_sobre_el_abox_del_pipeline():
    p = HRPipeline(mode="sim")
    p.warmup([get(3)])
    st = p.process(get(3))
    conforms, report = shapes.validate(abox.build_abox(st, list(p.agents)))
    assert conforms, report
