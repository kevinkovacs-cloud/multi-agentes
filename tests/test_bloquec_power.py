"""
Bloque C · C10 — min_window es umbral de DETECTABILIDAD; n_power da el n con potencia.

min_window: n ≥ 2·ln(2/δ)/margin² es el punto de potencia ≈ 50 % (no detección
garantizada). n_power(margin, δ, ν) = ⌈(sqrt(2 ln(4/δ)) + sqrt(ln(2/ν)))² / margin²⌉ es
el n por grupo y por ventana para que lcb_abs_diff_rates(...) > τ_b con probabilidad
≥ 1−ν cuando |Δ| = τ_b + margin.
"""
import numpy as np

from moav_hr.core import stats


def test_n_power_valores():
    assert stats.n_power(0.05) == 9530
    assert stats.n_power(0.10) == 2383


def test_min_window_no_cambia():
    assert stats.min_window(0.05, 0.10) == 738      # mismo valor de retorno que antes


def test_monte_carlo_potencia_al_menos_95():
    tau_b, margin, delta = 0.075, 0.10, 0.05
    n = stats.n_power(margin)                        # 2383 por grupo
    p_a = 0.5 + (tau_b + margin) / 2
    p_b = 0.5 - (tau_b + margin) / 2                 # |Δ| = τ_b + margin
    rng = np.random.default_rng(12345)
    ventanas = 400
    bloqueadas = 0
    for _ in range(ventanas):
        pos_a = int(rng.binomial(n, p_a))
        pos_b = int(rng.binomial(n, p_b))
        if stats.lcb_abs_diff_rates(pos_a, n, pos_b, n, delta) > tau_b:
            bloqueadas += 1
    assert bloqueadas / ventanas >= 0.95
