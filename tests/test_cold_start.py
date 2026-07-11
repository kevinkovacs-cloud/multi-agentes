"""A9 — arranque en frío de la reputación: prior declarado, donar exige historia."""
import pytest

from moav_hr.core.agent import MOACVAgent, TBOLayer, WIOLayer
from moav_hr.core.monitor import FairnessUtilityMonitor


def _maduro() -> MOACVAgent:
    return MOACVAgent("Maduro", "matcher", tbo=TBOLayer(training_runs=5),
                      wio=WIOLayer(production_feedback=[{"ok": True}]))


def _nacido() -> MOACVAgent:
    return MOACVAgent("Nacido", "matcher")


def test_sin_historia_devuelve_prior_r0():
    ag = _nacido()
    assert ag.reputation() == 0.8            # prior declarado (τ_r), ya no 1.0
    assert ag.reputation(r0=0.6) == 0.6      # r0 se respeta
    assert ag.windows_observed == 0


def test_born_no_puede_donar_pero_si_recibir():
    maduro, nacido = _maduro(), _nacido()
    maduro.learn({"x": 1}, "A", {"r": 1}, success=True)
    # el donante sin historia NO dona…
    with pytest.raises(ValueError, match="A9"):
        maduro.transfer_to(nacido)
    # …con m0 ventanas ya puede, y el receptor sin historia recibe sin problema
    for _ in range(3):
        maduro.record_window_fairness(0.9)
    rep = maduro.transfer_to(nacido)
    assert rep.accepted and len(nacido.theories) == 1


def test_cooperacion_exige_historia_del_donante():
    a, b = _maduro(), _maduro()
    a.learn({"x": 1}, "A", {"r": 1}, success=True)
    b.learn({"x": 2}, "A", {"r": 1}, success=True)
    for _ in range(3):
        a.record_window_fairness(0.9)        # solo A tiene historia
    with pytest.raises(ValueError, match="A9"):
        a.cooperate_with(b)                   # el donante es b (sin historia)
    for _ in range(3):
        b.record_window_fairness(0.9)
    assert a.cooperate_with(b).accepted


def test_reputacion_por_agente_discrimina_donantes():
    """N3: agentes con ventanas propias distintas → reputaciones distintas; el gating
    de Ω bloquea al de peor historia y no al otro."""
    mon = FairnessUtilityMonitor(tau=0.8)
    bueno, malo = _maduro(), _maduro()
    for _ in range(3):
        bueno.record_window_fairness(0.95)
        malo.record_window_fairness(0.50)
    assert bueno.reputation() != malo.reputation()
    assert mon.approve_sharing(bueno)
    assert not mon.approve_sharing(malo)
