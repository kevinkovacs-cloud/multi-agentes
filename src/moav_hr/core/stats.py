"""
Estadística con garantías para el Monitor Ω y la medición de μ (B6+A8).

Primitivo unificador: la COTA INFERIOR DE CONFIANZA (LCB). Los tres puntos de
intervención de Ω (auditoría de ventana — región 4; gate de evolución — región 7;
aprobación de compartición — Def. 9) son la misma pregunta: "¿la media de variables
acotadas está del lado correcto de un umbral, con confianza 1−δ?". Certificar con LCB
convierte reglas puntuales en garantías: P(bloqueo | Δ=0) ≤ δ por construcción.

Esta tanda usa Hoeffding (válido, conservador). Empirical-Bernstein queda declarada
como mejora pendiente de transcripción de la fuente (NO inventar constantes).
"""
from __future__ import annotations
import math
from typing import Optional

import numpy as np


def hoeffding_halfwidth(n: int, delta: float) -> float:
    """
    Semiancho de Hoeffding para la media de n variables en [0,1]:
    t = sqrt( ln(2/δ) / (2n) ). Con probabilidad ≥ 1−δ, |media − esperanza| ≤ t.
    """
    if n <= 0:
        raise ValueError("n debe ser positivo")
    if not (0 < delta < 1):
        raise ValueError("delta debe estar en (0,1)")
    return math.sqrt(math.log(2.0 / delta) / (2.0 * n))


def lcb_abs_diff_rates(pos_a: int, n_a: int, pos_b: int, n_b: int,
                       delta: float) -> float:
    """
    Cota inferior de confianza de |p_a − p_b| por unión de Hoeffding por grupo
    (δ/2 cada uno): max(0, |p̂_a − p̂_b| − t_a − t_b).

    Conservadora y válida: con prob. ≥ 1−δ, la verdadera |p_a − p_b| ≥ el valor
    devuelto. Es el certificado que usa el bloqueo del Monitor (B6).
    """
    if n_a <= 0 or n_b <= 0:
        raise ValueError("ambos grupos deben tener n > 0")
    p_hat_a, p_hat_b = pos_a / n_a, pos_b / n_b
    t_a = hoeffding_halfwidth(n_a, delta / 2.0)
    t_b = hoeffding_halfwidth(n_b, delta / 2.0)
    return max(0.0, abs(p_hat_a - p_hat_b) - t_a - t_b)


def empirical_bernstein_halfwidth(n: int, var_hat: float, delta: float) -> float:
    """
    Semiancho empirical-Bernstein (Maurer & Pontil 2009) — PENDIENTE.

    El enunciado exacto (constantes del Teorema 4) debe TRANSCRIBIRSE del paper antes
    de implementarse — NO inventar constantes. Hoeffding es el camino garantizado de
    esta tanda; Bernstein paga cuando la varianza empírica es chica.
    """
    raise NotImplementedError(
        "transcribir constantes de Maurer & Pontil (2009), Thm. 4 — no inventar")


def min_window(delta: float, margin: float) -> int:
    """
    Tamaño mínimo de ventana (por grupo) para que el certificado sea informativo:
    n ≥ 2·ln(2/δ) / margin². Detección garantizada requiere que la disparidad real
    supere el umbral por al menos `margin` (Δ_true − τ_b ≥ margin).
    """
    if not (0 < delta < 1) or margin <= 0:
        raise ValueError("delta ∈ (0,1) y margin > 0")
    return math.ceil(2.0 * math.log(2.0 / delta) / (margin ** 2))


def bootstrap_bca_log_mu(lotes_in: "list[float]", lotes_out: "list[float]",
                         n_boot: int = 2000, seed: Optional[int] = None,
                         confidence: float = 0.95):
    """
    IC BCa para log μ̂ = log( mean(b_out) / mean(b_in) ), remuestreando LOTES
    (pareados): la unidad de remuestreo es el lote, no la decisión — las decisiones
    dentro de un lote comparten prompt/contexto y no son independientes.

    Devuelve (log_mu_hat, (low, high)). Requiere medias positivas (μ es un cociente;
    con b_in ≈ 0 reportar b_out absoluto — caso degenerado de la Def. 10).
    """
    from scipy.stats import bootstrap as _bootstrap

    b_in = np.asarray(lotes_in, dtype=float)
    b_out = np.asarray(lotes_out, dtype=float)
    if b_in.shape != b_out.shape or b_in.ndim != 1 or len(b_in) < 3:
        raise ValueError("se requieren ≥3 lotes pareados (b_in_i, b_out_i)")
    if b_in.mean() <= 0 or b_out.mean() <= 0:
        raise ValueError("medias no positivas: reportar b_out absoluto (Def. 10 degenerada)")

    def _stat(in_s, out_s):
        return np.log(np.mean(out_s) / np.mean(in_s))

    rng = np.random.default_rng(seed)
    res = _bootstrap((b_in, b_out), _stat, paired=True, vectorized=False,
                     n_resamples=n_boot, confidence_level=confidence,
                     method="BCa", random_state=rng)
    log_mu = float(_stat(b_in, b_out))
    return log_mu, (float(res.confidence_interval.low),
                    float(res.confidence_interval.high))
