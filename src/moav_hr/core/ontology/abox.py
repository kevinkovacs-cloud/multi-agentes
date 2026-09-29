"""
ABox — instancias RDF generadas automáticamente desde el estado del pipeline (v13 §2.5).

Materializa teorías (región 5), decisiones y eventos de auditoría como tripletas
(sujeto, predicado, objeto) — homomorfismo de los estados operativos y los spans de
OpenTelemetry al grafo de procedencia. Reusa PROV-O. Reemplaza la construcción manual.
"""
from __future__ import annotations
from urllib.parse import quote

from rdflib import Graph, Literal
from rdflib.namespace import RDF, XSD

from moav_hr.core.ontology.ns import MOACV, PROV
from moav_hr.core.theory import q_canonical, serialize, theory_key

EVENT_CLASS = {
    "EventoDecision": MOACV.EventoDecision,
    "EventoEscalamiento": MOACV.EventoEscalamiento,
    "EventoTransferencia": MOACV.EventoTransferencia,
    "EventoBloqueoPorEquidad": MOACV.EventoBloqueoPorEquidad,
}


def _uri(kind: str, ident):
    return MOACV[f"{kind}/{ident}"]


def theory_iri(agent_name: str, t, q, kind: str = "Teoria"):
    """
    IRI estable por CLAVE de la teoría (bloque C · C3): agente + Q(Si) + A + Q(Sf).

    Reemplaza el IRI posicional {agente}-{i}, que cambiaba al reordenar la base
    (replace_all, en toda fusión) y rompía prov:wasDerivedFrom y la identificación M2M.
    Cada componente se escapa POR SEPARADO con quote(safe=''), incluido '/': el
    separador '/' no puede aparecer dentro de un componente, así que el esquema es
    inyectivo (el guion no se usa como separador). Mismo esquema para los nodos Si/Sf
    (kind="Si"/"Sf").
    """
    k1, k2, k3 = theory_key(t, q)
    return MOACV[f"{kind}/{quote(agent_name, safe='')}/{quote(k1, safe='')}"
                 f"/{quote(k2, safe='')}/{quote(k3, safe='')}"]


def _agent_node(g: Graph, name: str):
    u = _uri("Agente", name)
    g.add((u, RDF.type, MOACV.Agente))
    g.add((u, RDF.type, PROV.Agent))
    return u


def build_abox(state: dict, agents: list | None = None) -> Graph:
    g = Graph()
    g.bind("moacv", MOACV)
    g.bind("prov", PROV)
    trace = state.get("trace_id", "TRC-NA")

    # candidato (instancia HR)
    cand = state.get("candidate")
    cand_uri = None
    if cand is not None:
        cand_uri = _uri("Candidato", getattr(cand, "id", "x"))
        g.add((cand_uri, RDF.type, MOACV.Candidato))
        for prop, attr, dt in [("genero", "gender", XSD.string),
                               ("origen", "origin", XSD.string),
                               ("edad", "age", XSD.integer)]:
            val = getattr(cand, attr, None)
            if val is not None:
                g.add((cand_uri, MOACV[prop], Literal(val, datatype=dt)))

    # agentes + bases de teorías
    for a in (agents or []):
        au = _agent_node(g, a.name)
        g.add((au, MOACV.estado, Literal(a.maturity.label)))
        g.add((au, MOACV.capa, Literal(a.layers)))
        g.add((au, MOACV.reputacionEquidad, Literal(a.reputation(), datatype=XSD.double)))
        base = _uri("Base", a.name)
        g.add((base, RDF.type, MOACV.BaseDeConocimiento))
        g.add((au, MOACV.poseeBase, base))
        q = getattr(a.theories, "q", q_canonical)
        for t in a.theories.theories:
            tu = theory_iri(a.name, t, q)
            g.add((tu, RDF.type, MOACV.Teoria))
            g.add((tu, RDF.type, PROV.Entity))
            g.add((base, MOACV.contieneTeoria, tu))
            g.add((au, MOACV.registra, tu))
            g.add((tu, MOACV.P, Literal(int(t.p), datatype=XSD.integer)))
            g.add((tu, MOACV.K, Literal(int(t.k), datatype=XSD.integer)))
            # U sin redondeo (bloque C · C4): exacta en el grafo y en N-Triples/JSON-LD/XML.
            # OJO: el serializador Turtle de rdflib 7.6 abrevia xsd:double con "%e" (7 cifras);
            # la ida y vuelta exacta por Turtle queda como pregunta abierta (ver reporte C4).
            g.add((tu, MOACV.U, Literal(float(t.u), datatype=XSD.double)))
            g.add((tu, MOACV.usos, Literal(int(t.k_own), datatype=XSD.integer)))
            g.add((tu, MOACV.confiabilidad, Literal(round(t.reliability, 4), datatype=XSD.double)))
            # acción A (Def. 3) como propiedad — completa la tupla ⟨Si,A,Sf,P,K,U⟩ en el RDF
            g.add((tu, MOACV.accion, Literal(t.a)))
            si = theory_iri(a.name, t, q, kind="Si")
            g.add((si, RDF.type, MOACV.SituacionInicial))
            g.add((si, MOACV.representacionJSON, Literal(serialize(t.si))))
            g.add((tu, MOACV.aplicaEn, si))
            # situación final Sf (Def. 3) — necesaria para reconstruir/compartir la teoría (M2M)
            sf = theory_iri(a.name, t, q, kind="Sf")
            g.add((sf, RDF.type, MOACV.SituacionFinal))
            g.add((sf, MOACV.representacionJSON, Literal(serialize(t.sf))))
            g.add((tu, MOACV.aplicaEn, sf))

    # decisión final
    dec = state.get("decision")
    if dec is not None:
        du = _uri("Decision", trace)
        g.add((du, RDF.type, MOACV.Decision))
        g.add((du, RDF.type, PROV.Activity))
        g.add((du, MOACV.resultado, Literal(dec)))
        aud = state.get("auditor", {})
        if "adjusted_score" in aud:
            g.add((du, MOACV.scoreMatching, Literal(float(aud["adjusted_score"]), datatype=XSD.double)))
        # equidad: materializa el dictamen del Monitor en el RDF para que la explicación
        # se pueda derivar del grafo serializado y no del estado en memoria (ítem B).
        if "bias_score" in aud:
            g.add((du, MOACV.sesgoDetectado, Literal(float(aud["bias_score"]), datatype=XSD.double)))
        if "threshold" in aud:
            g.add((du, MOACV.umbralEquidad, Literal(float(aud["threshold"]), datatype=XSD.double)))
        if "bias_type" in aud:
            g.add((du, MOACV.tipoSesgo, Literal(str(aud["bias_type"]))))
        if "blocked" in aud:
            g.add((du, MOACV.bloqueada, Literal(bool(aud["blocked"]), datatype=XSD.boolean)))
        g.add((du, PROV.wasAssociatedWith, _agent_node(g, "Orchestrator")))
        if cand_uri is not None:
            g.add((du, PROV.used, cand_uri))
        # procedencia: la decisión deriva de las teorías registradas por los agentes
        for a in (agents or []):
            q = getattr(a.theories, "q", q_canonical)
            for t in a.theories.theories:
                g.add((du, PROV.wasDerivedFrom, theory_iri(a.name, t, q)))

    # eventos del audit trail (≡ spans OpenTelemetry)
    trail = state.get("trail")
    if trail is not None:
        prev_eu = None
        for j, ev in enumerate(trail.events):
            eu = _uri("Evento", f"{trace}-{j}")
            g.add((eu, RDF.type, EVENT_CLASS.get(ev.event_type, MOACV.EventoDeAuditoria)))
            g.add((eu, RDF.type, PROV.Activity))
            g.add((eu, MOACV.timestamp, Literal(float(ev.ts), datatype=XSD.double)))
            # ordinal explícito: ancla la secuencia al índice de ejecución, no al orden de
            # triples ni al timestamp (que puede colisionar). Recuperar con ORDER BY ?orden.
            g.add((eu, MOACV.ordenEjecucion, Literal(j, datatype=XSD.integer)))
            g.add((eu, MOACV.tipo, Literal(ev.action)))
            # encadenado causal PROV-O entre eventos consecutivos (refuerza el orden)
            if prev_eu is not None:
                g.add((eu, PROV.wasInformedBy, prev_eu))
            ag = _agent_node(g, ev.agent)
            g.add((eu, PROV.wasAssociatedWith, ag))
            g.add((ag, MOACV.generaEvento, eu))
            prev_eu = eu
    return g


def to_turtle(state: dict, agents: list | None = None) -> str:
    return build_abox(state, agents).serialize(format="turtle")
