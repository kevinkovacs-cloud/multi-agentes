"""Tests de la ontología (§2.5): TBox, ABox automático, validación SHACL y consultas SPARQL."""
from moav_hr.core.ontology.tbox import build_tbox
from moav_hr.core.ontology import abox, shapes, queries
from moav_hr.instances.hr.synthetic import get
from moav_hr.instances.hr.pipeline import HRPipeline


def _state():
    p = HRPipeline(mode="sim")
    p.warmup([get(3)])
    return p.process(get(3)), list(p.agents)


def test_tbox_tiene_clases_y_props():
    g = build_tbox()
    assert len(g) > 30   # clases + jerarquías + propiedades + alineación PROV-O


def test_abox_se_genera_automaticamente():
    st, agents = _state()
    g = abox.build_abox(st, agents)
    assert len(g) > 0


def test_shacl_conforme():
    st, agents = _state()
    conforms, report = shapes.validate(abox.build_abox(st, agents))
    assert conforms, report


def test_sparql_interoperabilidad():
    st, agents = _state()
    g = abox.build_abox(st, agents)
    prov = queries.run(g, queries.Q_DECISIONS_PROVENANCE)
    assert len(prov) >= 1
    esc = queries.run(g, queries.Q_ESCALATIONS)
    assert int(esc[0]["escalamientos"]) >= 1   # Fátima escala a revisión humana
