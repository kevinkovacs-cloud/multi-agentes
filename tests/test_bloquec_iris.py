"""
Bloque C · C3 + C13 — IRIs de teorías (y de sus Si/Sf) estables por CLAVE.

C3: antes el IRI era posicional ({agente}-{i}, con i = índice en la base): replace_all
(que corre en toda fusión) reordena la base y la MISMA teoría cambiaba de IRI, lo que
rompía prov:wasDerivedFrom y la identificación M2M.
C13: la clave completa escapada hacía IRIs muy largos; ahora el IRI es
{kind}/{agente}/{h}, con h = 16 hex del sha256 de la clave JSON [Q(Si), A, Q(Sf)], y la
clave completa queda en el literal moacv:clave (sin pérdida).
"""
import json
import re
from types import SimpleNamespace

from rdflib import Graph

from moav_hr.core.ontology import abox
from moav_hr.core.ontology.ns import MOACV
from moav_hr.core.ontology.sharing_rdf import theories_from_turtle, theories_to_turtle
from moav_hr.core.theory import Theory, TheoryBase, q_canonical, theory_key


def _agent(base, name="Matcher"):
    """Lo mínimo que build_abox lee de un agente."""
    return SimpleNamespace(name=name, maturity=SimpleNamespace(label="Trained"),
                           layers="BIO+TBO", reputation=lambda: 0.9, theories=base)


def _iri_by_action(g):
    """acción (literal) → IRI de la teoría que la registra."""
    return {str(o): s for s, o in g.subject_objects(MOACV.accion)}


def _base():
    base = TheoryBase()
    for a in ("A1", "A2", "A3"):
        base.add(Theory(si={"x": 1}, a=a, sf={"r": a}, p=1, k=2, u=0.5))
    return base


def test_misma_teoria_mismo_iri_tras_reordenar():
    base = _base()
    antes = _iri_by_action(abox.build_abox({}, [_agent(base)]))
    m2m_antes = _iri_by_action(Graph().parse(
        data=theories_to_turtle(base.theories, agent="Matcher"), format="turtle"))
    base.replace_all(list(reversed(base.theories)))      # lo que hace toda fusión
    despues = _iri_by_action(abox.build_abox({}, [_agent(base)]))
    m2m_despues = _iri_by_action(Graph().parse(
        data=theories_to_turtle(base.theories, agent="Matcher"), format="turtle"))
    assert len(antes) == 3
    assert antes == despues
    assert m2m_antes == m2m_despues


def test_iri_inyectivo_con_guiones_y_barras():
    q = lambda s: s["k"]                     # cuantización que devuelve el str crudo

    def T(si, a, sf="z"):
        return Theory(si={"k": si}, a=a, sf={"k": sf})

    # con '-' como separador, "x-2"+"3" y "x"+"2-3" colisionaban
    assert abox.theory_iri("a", T("x-2", "3"), q) != abox.theory_iri("a", T("x", "2-3"), q)
    # '/' dentro de un componente no se confunde con un separador
    assert abox.theory_iri("a", T("x/2", "3"), q) != abox.theory_iri("a", T("x", "2/3"), q)
    assert abox.theory_iri("a/b", T("c", "3"), q) != abox.theory_iri("a", T("b/c", "3"), q)
    # la misma teoría (misma clave) da el mismo IRI
    assert abox.theory_iri("a", T("x", "1"), q) == abox.theory_iri("a", T("x", "1"), q)
    # Si/Sf usan el mismo hash con otro prefijo de tipo
    t = T("x", "1")
    teoria = str(abox.theory_iri("a", t, q)).split("/Teoria/")[1]
    assert str(abox.theory_iri("a", t, q, kind="Si")).split("/Si/")[1] == teoria
    assert str(abox.theory_iri("a", t, q, kind="Sf")).split("/Sf/")[1] == teoria


def test_iri_corto_por_hash():
    t = Theory(si={"edu": "Doctorado", "exp_band": "senior", "skills_match": 0},
               a="ADVANCE", sf={"outcome": "ADVANCE"})
    iri = str(abox.theory_iri("Matcher", t, q_canonical))
    assert re.fullmatch(r".*/Teoria/Matcher/[0-9a-f]{16}", iri)


def test_clave_recuperable_igual_a_theory_key():
    base = _base()
    for g in (abox.build_abox({}, [_agent(base)]),
              Graph().parse(data=theories_to_turtle(base.theories, agent="Matcher"),
                            format="turtle")):
        claves = {str(g.value(s, MOACV.accion)): tuple(json.loads(str(o)))
                  for s, o in g.subject_objects(MOACV.clave)}
        assert claves == {t.a: theory_key(t, q_canonical) for t in base.theories}


def test_ida_y_vuelta_m2m_con_iris_por_clave():
    base = _base()
    rec = theories_from_turtle(theories_to_turtle(base.theories, agent="Matcher"))
    firma = lambda ts: sorted((t.a, t.p, t.k, t.u, str(t.si), str(t.sf)) for t in ts)
    assert firma(rec) == firma(base.theories)
