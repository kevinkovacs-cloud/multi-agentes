"""
Bloque C · C4 + C12 — U se exporta sin pérdida y se exportan los usos propios (k_own).

C4: antes abox redondeaba U a 4 decimales (y sharing_rdf a 6); se agregó la propiedad
de datos `usos` = k_own (declarada en la TBox con el mismo patrón que P y K). K se sigue
exportando igual. Al importar, k_own se reconstruye desde `usos` si está.

C12: con xsd:double, el serializador Turtle de rdflib 7.6 abrevia a 7 cifras ("%e":
6.666667e-01). Decisión (Claude chat, 29/09): U como xsd:decimal con Decimal(repr(u)),
que vuelve exacto porque repr(float) es la representación más corta que redondea al
mismo float. El M2M y el paso [7] del demo siguen en Turtle (pedido de Becerra).
"""
from decimal import Decimal
from types import SimpleNamespace

import pytest
from rdflib import Graph, Literal
from rdflib.namespace import OWL, RDF, RDFS, XSD

from moav_hr.core.ontology import abox, shapes
from moav_hr.core.ontology.ns import MOACV
from moav_hr.core.ontology.sharing_rdf import theories_from_turtle, theories_to_turtle
from moav_hr.core.ontology.tbox import build_tbox
from moav_hr.core.theory import Theory, TheoryBase
from moav_hr.instances.hr.pipeline import HRPipeline
from moav_hr.instances.hr.synthetic import get

VALORES = [2 / 3, 0.1, 1 / 7]


def _teoria(u=2 / 3):
    # tras una fusión: K expuesto (celda) = 10, usos propios = 4
    return Theory(si={"x": 1}, a="ADVANCE", sf={"r": "ok"}, p=3, k=10, u=u, k_own=4)


def _agent(base):
    return SimpleNamespace(name="Matcher", maturity=SimpleNamespace(label="Trained"),
                           layers="BIO+TBO", reputation=lambda: 0.9, theories=base)


def _abox(u):
    base = TheoryBase()
    base.add(_teoria(u))
    return abox.build_abox({}, [_agent(base)])


@pytest.mark.parametrize("u", VALORES)
def test_u_ida_y_vuelta_exacta_por_turtle(u):
    """Criterio (a) de C4, cerrado en C12 (antes xfail): exacto por Turtle."""
    rec = theories_from_turtle(theories_to_turtle([_teoria(u)], agent="Matcher"))
    assert rec[0].u == u                                                     # M2M
    ttl = _abox(u).serialize(format="turtle")
    assert [float(o) for o in Graph().parse(data=ttl, format="turtle").objects(None, MOACV.U)] == [u]


def test_u_exacta_en_el_grafo_y_en_ntriples():
    g = _abox(2 / 3)
    assert [float(o) for o in g.objects(None, MOACV.U)] == [2 / 3]
    nt = g.serialize(format="nt")
    assert [float(o) for o in Graph().parse(data=nt, format="nt").objects(None, MOACV.U)] == [2 / 3]


def test_u_es_xsd_decimal_en_abox_m2m_y_tbox():
    assert [o.datatype for o in _abox(2 / 3).objects(None, MOACV.U)] == [XSD.decimal]
    g = Graph().parse(data=theories_to_turtle([_teoria()], agent="Matcher"), format="turtle")
    assert [o.datatype for o in g.objects(None, MOACV.U)] == [XSD.decimal]
    assert (MOACV.U, RDFS.range, XSD.decimal) in build_tbox()


def test_usos_existe_y_vale_k_own():
    g = Graph().parse(data=theories_to_turtle([_teoria()], agent="Matcher"), format="turtle")
    assert [int(o) for o in g.objects(None, MOACV.usos)] == [4]
    assert [int(o) for o in g.objects(None, MOACV.K)] == [10]      # K sin cambios
    assert [int(o) for o in _abox(2 / 3).objects(None, MOACV.usos)] == [4]
    # la importación reconstruye k_own desde `usos`
    t = theories_from_turtle(g)[0]
    assert (t.p, t.k, t.k_own) == (3, 10, 4)
    # declarada en la TBox como propiedad de datos
    assert (MOACV.usos, RDF.type, OWL.DatatypeProperty) in build_tbox()


def test_shacl_valida_u_en_0_1_con_decimal():
    p = HRPipeline(mode="sim")
    p.warmup([get(3)])
    st = p.process(get(3))
    g = abox.build_abox(st, list(p.agents))
    conforms, report = shapes.validate(g)
    assert conforms, report                        # el ABox del pipeline es conforme
    # y la restricción U ∈ [0,1] sigue activa con xsd:decimal
    s = next(iter(g.subjects(MOACV.U, None)))
    g.set((s, MOACV.U, Literal(Decimal("1.5"), datatype=XSD.decimal)))
    conforms, report = shapes.validate(g)
    assert not conforms
    assert "MaxInclusive" in report
