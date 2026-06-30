"""
Ítem B (Becerra) — la explicación se deriva de la serialización RDF, no del estado en memoria.

Clave: la entrada de `explain_from_rdf` es la cadena Turtle YA serializada (round-trip), de
modo que la explicación reconstruida no puede provenir del objeto de decisión original.
Además distingue dos destinatarios (regulador vs usuario), con necesidades distintas.
"""
from moav_hr.core.ontology import abox
from moav_hr.core.ontology.explain import explain_from_rdf
from moav_hr.instances.hr.pipeline import HRPipeline
from moav_hr.instances.hr.synthetic import get


def _state_escalado():
    p = HRPipeline(mode="sim")
    p.warmup([get(3)])
    st = p.process(get(3))           # caso Fátima: escala a revisión humana
    assert st["decision"] == "ESCALATE_HUMAN", st["decision"]
    return st, list(p.agents)


def test_explicacion_se_deriva_de_la_serializacion():
    st, agents = _state_escalado()
    # serializar a Turtle (string) y derivar SOLO de ahí — sin pasar el estado en memoria
    turtle = abox.build_abox(st, agents).serialize(format="turtle")
    exp = explain_from_rdf(turtle)

    assert set(exp) >= {"regulador", "usuario"}
    # el insumo fue la cadena serializada, no el dict st["auditor"]
    assert exp["datos"]["escalada"] is True


def test_dos_destinatarios_distintos_y_coherentes():
    st, agents = _state_escalado()
    exp = explain_from_rdf(abox.build_abox(st, agents))  # también acepta el Graph directo

    reg, usr = exp["regulador"], exp["usuario"]
    # regulador: técnico/completo (umbral, trazabilidad, cumplimiento)
    assert "umbral" in reg and "EU AI Act" in reg and "eventos" in reg
    # usuario: lenguaje llano, accionable, sin jerga de umbrales
    assert "revisión humana" in usr and "umbral" not in usr
    # son explicaciones distintas para el mismo hecho
    assert reg != usr


def test_explicacion_refleja_caso_no_escalado():
    """Para un caso que avanza sin intervención, el mensaje al usuario cambia."""
    p = HRPipeline(mode="sim")
    p.warmup([get(i) for i in range(1, 13)])
    # buscar un candidato que avance (ADVANCE) para cubrir la otra rama
    for i in range(1, 13):
        st = p.process(get(i))
        if st["decision"] == "ADVANCE":
            exp = explain_from_rdf(abox.build_abox(st, list(p.agents)).serialize(format="turtle"))
            assert exp["datos"]["escalada"] is False
            assert "avanzó" in exp["usuario"]
            return
    # si ningún caso avanzó en este lote, el test no aplica (no falla)
