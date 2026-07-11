"""
B6+A8 — certificación estadística del Monitor: bajo H₀ el bloqueo certificado tiene
FPR ≤ δ (el puntual no), y con disparidad real grande el certificado sí bloquea.
"""
import numpy as np
import pytest

from moav_hr.core import stats
from moav_hr.core.agent import MOACVAgent
from moav_hr.core.monitor import FairnessUtilityMonitor


def _window(rng, n_per_group: int, rate_a: float, rate_b: float) -> list[dict]:
    recs = []
    for group, rate in (("A", rate_a), ("B", rate_b)):
        adv = rng.random(n_per_group) < rate
        recs += [{"origin_group": group, "gender": "F", "true_qual": 0.9,
                  "score": 0.8, "bias_risk": "low",
                  "decision": "ADVANCE" if a else "REJECT"} for a in adv]
    return recs


def test_fpr_bajo_h0_certificado_menor_delta_y_puntual_lo_supera():
    """500 ventanas H₀ (tasas iguales 0.5, n=200/grupo): el monitor puntual bloquea
    ruido muy por encima de δ; el certificado queda ≤ δ + margen binomial."""
    mon = FairnessUtilityMonitor(disparity_threshold=0.075)
    rng = np.random.default_rng(20260711)
    delta = 0.05
    sims = 500
    bloqueos_punt = bloqueos_cert = 0
    for _ in range(sims):
        recs = _window(rng, 200, 0.5, 0.5)
        if mon.audit_window(recs).blocked:
            bloqueos_punt += 1
        if mon.audit_window(recs, certified=True, delta=delta).blocked:
            bloqueos_cert += 1
    fpr_punt = bloqueos_punt / sims
    fpr_cert = bloqueos_cert / sims
    margen_binomial = 3 * (delta * (1 - delta) / sims) ** 0.5    # ~0.029
    assert fpr_cert <= delta + margen_binomial, f"FPR certificado {fpr_cert}"
    assert fpr_punt > delta, f"el puntual debería superar δ (documenta el porqué " \
                             f"del certificado); dio {fpr_punt}"


def test_con_disparidad_grande_y_n_suficiente_el_certificado_bloquea():
    mon = FairnessUtilityMonitor(disparity_threshold=0.075)
    rng = np.random.default_rng(7)
    recs = _window(rng, 400, 0.9, 0.3)          # Δ real = 0.6
    audit = mon.audit_window(recs, certified=True, delta=0.05)
    assert audit.certified and audit.lcb is not None
    assert audit.blocked
    assert audit.lcb > mon.disparity_threshold


def test_min_window_coherente_con_la_deteccion():
    """Con margen = Δ_true − τ_b y n ≥ min_window por grupo, el certificado detecta."""
    delta, tau_b, d_true = 0.05, 0.075, 0.6
    margin = d_true - tau_b
    n_min = stats.min_window(delta, margin)
    assert n_min >= 1
    mon = FairnessUtilityMonitor(disparity_threshold=tau_b)
    rng = np.random.default_rng(11)
    # n holgado sobre el mínimo para absorber ruido de muestreo del test
    recs = _window(rng, max(n_min, 60) * 2, 0.8, 0.2)
    assert mon.audit_window(recs, certified=True, delta=delta).blocked


def test_certificado_exige_dos_grupos():
    mon = FairnessUtilityMonitor()
    recs = [{"origin_group": "A", "gender": "F", "true_qual": 0.9, "score": 0.8,
             "bias_risk": "low", "decision": "ADVANCE"}] * 10
    with pytest.raises(ValueError):
        mon.audit_window(recs, certified=True)


def test_gate_evolution_certificado_exige_evidencia():
    mon = FairnessUtilityMonitor(tau=0.8)
    ag = MOACVAgent("X", "matcher")
    assert not mon.gate_evolution(ag, certified=True)          # sin historia: no certifica
    for _ in range(3):
        ag.record_window_fairness(0.85)                        # media 0.85, m=3
    # LCB = 0.85 − sqrt(ln(40)/6) ≈ 0.85 − 0.78 < 0.8 → aún sin evidencia suficiente
    assert not mon.gate_evolution(ag, certified=True, m=5, delta=0.05)
    for _ in range(200):
        ag.record_window_fairness(0.95)
    assert mon.gate_evolution(ag, certified=True, m=200, delta=0.05)
    # el modo puntual (default) se mantiene
    assert mon.gate_evolution(ag)


def test_stats_basicos():
    assert stats.hoeffding_halfwidth(200, 0.05) == pytest.approx(
        (np.log(2 / 0.05) / 400) ** 0.5)
    assert stats.lcb_abs_diff_rates(100, 200, 100, 200, 0.05) == 0.0
    with pytest.raises(NotImplementedError):
        stats.empirical_bernstein_halfwidth(100, 0.1, 0.05)
    log_mu, (lo, hi) = stats.bootstrap_bca_log_mu(
        [0.10, 0.11, 0.09, 0.10, 0.12], [0.05, 0.06, 0.05, 0.04, 0.06],
        n_boot=500, seed=1)
    assert lo <= log_mu <= hi and log_mu < 0
