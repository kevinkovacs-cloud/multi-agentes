"""Bloque D · D4a: transición de estado gobernada por gate_evolution (Def. 12)."""
import warnings

import pytest

from moav_hr.core.agent import MOACVAgent, TBOLayer
from moav_hr.core.audit.trail import AuditTrail
from moav_hr.core.lifecycle import MaturityState, Region
from moav_hr.core.monitor import FairnessMonitor


def _agente():
    return MOACVAgent("A", "matcher", tbo=TBOLayer(training_runs=0))


def test_gate_aprueba_y_el_agente_recorre_el_ciclo():
    ag, mon, trail = _agente(), FairnessMonitor(tau=0.8), AuditTrail("TRC-T")
    for _ in range(3):
        ag.record_window_fairness(0.95)
    esperado = [MaturityState.NOVATO, MaturityState.TRAINED, MaturityState.MATURE]
    for estado in esperado:
        assert ag.advance(mon, trail=trail) is True
        assert ag.maturity == estado
    assert ag.tbo.training_runs == 3 and len(ag.wio.production_feedback) == 1
    assert ag.advance(mon, trail=trail) is False          # Mature es el tope
    evs = [e for e in trail.events if e.region == int(Region.EVOLUTION)]
    assert [e.action for e in evs] == ["transicion_de_estado"] * 3
    assert [e.detail["hacia"] for e in evs] == ["novato", "trained", "mature"]


def test_gate_rechaza_y_el_agente_no_avanza():
    ag, mon, trail = _agente(), FairnessMonitor(tau=0.8), AuditTrail("TRC-T")
    ag.record_window_fairness(0.5)                      # r = 0.5 < τ
    assert ag.advance(mon, trail=trail) is False
    assert ag.maturity == MaturityState.BORN and ag.tbo.training_runs == 0
    (ev,) = trail.events
    assert ev.region == int(Region.EVOLUTION) and ev.action == "transicion_denegada"
    assert ev.detail["aprobado"] is False


def test_gate_certificado_sin_historia_no_avanza():
    ag, mon = _agente(), FairnessMonitor(tau=0.8)
    with pytest.warns(UserWarning, match="m_min"):
        assert ag.advance(mon, certified=True) is False
    assert ag.maturity == MaturityState.BORN


def test_advance_no_cambia_el_calculo_de_maturity():
    ag = _agente()
    ag.tbo.training_runs = 2
    assert ag.maturity == MaturityState.NOVATO
    with warnings.catch_warnings():
        warnings.simplefilter("error")                  # el modo puntual no advierte
        ag.record_window_fairness(1.0)
        assert ag.advance(FairnessMonitor(tau=0.8)) is True
    assert ag.tbo.training_runs == 3 and ag.maturity == MaturityState.TRAINED
