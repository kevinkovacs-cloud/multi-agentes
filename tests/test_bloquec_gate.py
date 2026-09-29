"""
Bloque C · C7 — gate de evolución certificado: cuándo es alcanzable.

gate_evolution(certified=True) exige r̄ − sqrt(ln(2/δ)/(2n)) ≥ τ con n ≤ m. Con el
default m = 5 y δ = 0.05 el semiancho es 0.607: se exigiría una media ≥ 1.407 y ningún
agente puede pasar. stats.m_min_gate da el mínimo n = ⌈ln(2/δ)/(2(r̄−τ)²)⌉ y el gate
avisa (warning) cuando n < m_min(1.0). El valor de retorno no cambia.
"""
import warnings

import pytest

from moav_hr.core import stats
from moav_hr.core.agent import MOACVAgent
from moav_hr.core.monitor import FairnessUtilityMonitor


def _agente(n_ventanas_perfectas):
    ag = MOACVAgent("X", "matcher")
    for _ in range(n_ventanas_perfectas):
        ag.record_window_fairness(1.0)
    return ag


def test_m_min_gate_valores():
    assert stats.m_min_gate(1.0, 0.8, 0.05) == 47
    assert stats.m_min_gate(0.95, 0.8, 0.05) == 82
    with pytest.raises(ValueError):
        stats.m_min_gate(0.8, 0.8, 0.05)          # r̄ ≤ τ: ningún n alcanza


def test_warning_con_m5_y_5_ventanas_perfectas():
    mon = FairnessUtilityMonitor(tau=0.8)
    with pytest.warns(UserWarning, match=r"m_min\(1\.0\)=47"):
        aprobado = mon.gate_evolution(_agente(5), certified=True, m=5, delta=0.05)
    assert aprobado is False                      # el retorno no cambia


def test_sin_warning_y_aprueba_con_m47_y_47_ventanas_perfectas():
    mon = FairnessUtilityMonitor(tau=0.8)
    # gate_evolution toma las últimas m ventanas: m=47 explícito
    with warnings.catch_warnings():
        warnings.simplefilter("error")            # cualquier warning haría fallar
        aprobado = mon.gate_evolution(_agente(47), certified=True, m=47, delta=0.05)
    assert aprobado is True
