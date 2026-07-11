"""
Calibración de scores (C4) — la definición OPERATIVA de "capa TBO completada".

Hasta ahora "calibrar el LLM (TBO)" no estaba definido en ningún documento. Este
módulo lo vuelve un criterio verificable: capa TBO completada = ECE reportado ANTES y
DESPUÉS de calibrar sobre el conjunto de desarrollo (Platt o isotónica).

En esta tanda NO se aplica a ningún LLM (eso es del Eje 2): se entrega el instrumento
con tests sobre scores sintéticos de sesgo conocido.
"""
from __future__ import annotations

import numpy as np


def platt(scores: "list[float]", labels: "list[int]"):
    """
    Calibración de Platt: regresión logística 1-D sobre el score.
    Devuelve una función score→probabilidad calibrada.
    """
    from sklearn.linear_model import LogisticRegression
    X = np.asarray(scores, dtype=float).reshape(-1, 1)
    y = np.asarray(labels, dtype=int)
    clf = LogisticRegression(max_iter=1000).fit(X, y)

    def transform(new_scores: "list[float]") -> np.ndarray:
        return clf.predict_proba(
            np.asarray(new_scores, dtype=float).reshape(-1, 1))[:, 1]

    return transform


def isotonic(scores: "list[float]", labels: "list[int]"):
    """
    Calibración isotónica: regresión monótona no paramétrica score→probabilidad.
    Más flexible que Platt; requiere más datos para no sobreajustar.
    """
    from sklearn.isotonic import IsotonicRegression
    iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip").fit(
        np.asarray(scores, dtype=float), np.asarray(labels, dtype=int))

    def transform(new_scores: "list[float]") -> np.ndarray:
        return iso.predict(np.asarray(new_scores, dtype=float))

    return transform


def ece(scores: "list[float]", labels: "list[int]", bins: int = 10) -> float:
    """
    Expected Calibration Error: promedio ponderado de |acc(bin) − conf(bin)| sobre
    bins de confianza. ECE ≈ 0 ⟺ el score se puede leer como probabilidad.
    """
    s = np.asarray(scores, dtype=float)
    y = np.asarray(labels, dtype=int)
    if s.shape != y.shape or s.ndim != 1 or len(s) == 0:
        raise ValueError("scores y labels deben ser vectores alineados no vacíos")
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = len(s)
    out = 0.0
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (s >= lo) & (s < hi) if i < bins - 1 else (s >= lo) & (s <= hi)
        if not mask.any():
            continue
        conf = s[mask].mean()
        acc = y[mask].mean()
        out += (mask.sum() / total) * abs(acc - conf)
    return round(float(out), 6)
