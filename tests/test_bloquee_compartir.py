"""Bloque E · E3: compartición en el modo LLC con axiomas, can_donate y gate de Ω v2."""
from moav_hr.core.ciclo_llc import AgenteLLC
from moav_hr.core.compartir_llc import compartir
from moav_hr.core.lifecycle import MaturityState
from moav_hr.core.monitor import FairnessMonitor
from moav_hr.core.ontology.ns import PROV
from moav_hr.core.ontology.sharing_rdf import procedencia_compartida
from moav_hr.core.theory import theory_key, violaciones_invariante_llc

SI = {"skills_match": 1, "exp_band": "senior", "edu": "Licenciatura", "seniority_ok": True}
OK, NO = {"calificado": True}, {"calificado": False}
PAREJO = [{"origin_group": g, "decision": d} for g in ("AR", "no-AR")
          for d in ("ADVANCE", "REJECT") * 10]
SESGADO = [{"origin_group": "AR", "decision": "ADVANCE"}] * 40 + \
          [{"origin_group": "no-AR", "decision": "REJECT"}] * 40


def _acierto(t):
    return (t.a == "ADVANCE") == t.sf["calificado"]


def _agente(nombre, estado, ventanas=3):
    ag = AgenteLLC(nombre, "matcher")
    ag._estado = estado                     # solo en tests; las demos usan estados ganados
    for _ in range(ventanas):
        ag.record_window_fairness(0.9)
    return ag


def _registrar(ag, sf, veces):
    for _ in range(veces):
        ag.theories.registrar_llc(SI, "ADVANCE", sf, 1.0 if sf["calificado"] else 0.0)


def test_colaboracion_aceptada_conserva_el_invariante_y_registra_similares():
    a, b = _agente("A", MaturityState.MATURE), _agente("B", MaturityState.NOVATO)
    _registrar(a, OK, 3)
    _registrar(b, NO, 2)                    # misma (Si, A), otra Sf → similar
    r = compartir("colaboracion", a, b, FairnessMonitor(), {"A": PAREJO}, 3, 0.05, _acierto)
    assert r["aceptada"] and r["conteo"]["similar"] == 1
    assert violaciones_invariante_llc(b.theories) == []
    por_sf = {t.sf["calificado"]: (t.p, t.k) for t in b.theories.theories}
    assert por_sf == {True: (3, 5), False: (2, 5)}           # Alg. 4.10
    assert {round(t.u, 6) for t in b.theories.theories} == {round(4 / 7, 6)}   # U(Si, A)
    g = procedencia_compartida("B", "A", b.theories.theories, a.theories.theories)
    assert len(list(g.triples((None, PROV.wasDerivedFrom, None)))) == 1


def test_rechazos_por_axioma_historia_y_evidencia_de_sesgo():
    mon = FairnessMonitor()
    a, b = _agente("A", MaturityState.MATURE), _agente("B", MaturityState.NOVATO)
    r = compartir("colaboracion", b, a, mon, {"B": PAREJO}, 3, 0.05)     # hacia un estado superior
    assert not r["aceptada"] and r["axioma"] and "[b]" in r["axioma"]
    r = compartir("cooperacion", a, b, mon, {"A": PAREJO, "B": PAREJO}, 3, 0.05)   # estados distintos
    assert not r["aceptada"] and "[a]" in r["axioma"]
    nuevo = _agente("N", MaturityState.MATURE, ventanas=0)
    r = compartir("colaboracion", nuevo, b, mon, {"N": PAREJO}, 3, 0.05)
    assert not r["aceptada"] and "A9" in r["motivo"]
    r = compartir("colaboracion", a, b, mon, {"A": SESGADO}, 3, 0.05)
    assert not r["aceptada"] and "evidencia de sesgo" in r["motivo"]
    assert len(b.theories) == 0                                          # nada se fusionó


def test_cooperacion_entre_pares_del_mismo_estado():
    b, c = _agente("B", MaturityState.NOVATO), _agente("C", MaturityState.NOVATO)
    _registrar(b, OK, 1)
    _registrar(c, NO, 1)
    r = compartir("cooperacion", b, c, FairnessMonitor(), {"B": PAREJO, "C": PAREJO}, 3, 0.05,
                  _acierto)
    assert r["aceptada"]
    claves_b = {theory_key(t, b.theories.q) for t in b.theories.theories}
    assert claves_b == {theory_key(t, c.theories.q) for t in c.theories.theories}   # base común
    assert violaciones_invariante_llc(b.theories) == [] == violaciones_invariante_llc(c.theories)
    c2 = _agente("C2", MaturityState.NOVATO, ventanas=1)
    r = compartir("cooperacion", b, c2, FairnessMonitor(), {"B": PAREJO, "C2": PAREJO}, 3, 0.05)
    assert not r["aceptada"] and "C2" in r["motivo"]                     # el par sin historia
