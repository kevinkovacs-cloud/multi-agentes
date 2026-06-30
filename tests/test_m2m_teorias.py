"""
Compartición de teorías máquina a máquina (M2M) vía la ontología (obs. Becerra).

Demuestra que un agente puede compartir su base de teorías ⟨Si,A,Sf,P,K,U⟩ de forma
estándar: se serializa a RDF/Turtle y OTRO agente la reconstruye **desde el RDF**, sin
compartir objetos en memoria ni depender del mismo framework.
"""
import json

from moav_hr.core.theory import Theory, TheoryBase
from moav_hr.core.ontology.sharing_rdf import theories_to_turtle, theories_from_turtle
from moav_hr.core.ontology import abox
from moav_hr.instances.hr.pipeline import HRPipeline
from moav_hr.instances.hr.synthetic import get


def _sample():
    return [
        Theory(si={"skill": "python", "exp": 5}, a="ADVANCE", sf={"outcome": "ADVANCE"}, p=3, k=4, u=0.9),
        Theory(si={"skill": "java", "exp": 1}, a="REJECT", sf={"outcome": "REJECT"}, p=2, k=2, u=0.8),
    ]


def _key(t: Theory):
    return (json.dumps(t.si, sort_keys=True), t.a, json.dumps(t.sf, sort_keys=True),
            t.p, t.k, round(t.u, 6))


def test_m2m_roundtrip_reconstruye_la_tupla_completa():
    A = _sample()
    turtle = theories_to_turtle(A, agent="AgenteA")
    # B reconstruye SOLO desde el string Turtle (no accede a los objetos de A)
    B = theories_from_turtle(turtle)
    assert {_key(t) for t in B} == {_key(t) for t in A}


def test_m2m_la_base_reconstruida_es_funcional():
    turtle = theories_to_turtle(_sample(), agent="AgenteA")
    baseB = TheoryBase()                      # agente B "vacío", otra base
    for t in theories_from_turtle(turtle):
        baseB.add(t)
    assert len(baseB) == 2
    # la experiencia heredada del RDF sirve para decidir (Def. 4: selección por ranking)
    sel = baseB.select({"skill": "python", "exp": 5})
    assert sel is not None and sel.a == "ADVANCE"


def test_importa_teorias_desde_un_abox_completo():
    """Mismo vocabulario §2.5: el importador también lee teorías de un ABox completo."""
    p = HRPipeline(mode="sim")
    p.warmup([get(3)])
    st = p.process(get(3))
    turtle = abox.build_abox(st, list(p.agents)).serialize(format="turtle")
    teorias = theories_from_turtle(turtle)
    assert len(teorias) >= 1
    t = teorias[0]
    assert isinstance(t.si, dict) and t.a and isinstance(t.sf, dict)
