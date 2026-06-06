"""
Métricas de fairness a nivel de decisión y de pipeline.

Incluye las métricas canónicas (demographic parity, aproximación de equalized odds)
y el "error vs ground-truth por grupo" usado para el caso basal — la subestimación
sistemática de grupos protegidos respecto a su calificación real.
"""
from __future__ import annotations
from typing import Iterable

import numpy as np

POSITIVE = ("ADVANCE", "ESCALATE_HUMAN")  # "en proceso" = no rechazado


def _rate(decisions: Iterable[str]) -> float:
    decisions = list(decisions)
    if not decisions:
        return 0.0
    pos = sum(1 for d in decisions if d in POSITIVE)
    return pos / len(decisions)


def demographic_parity(records: list[dict], attr: str) -> dict:
    """
    Demographic Parity Δ = diferencia entre la mayor y la menor tasa de avance
    entre grupos del atributo protegido. Ideal: Δ < 0.10 (regla del 80%).

    records: dicts con keys `attr` y "decision".
    """
    groups: dict[str, list[str]] = {}
    for r in records:
        groups.setdefault(str(r[attr]), []).append(r["decision"])
    rates = {g: _rate(ds) for g, ds in groups.items()}
    if len(rates) < 2:
        return {"delta": 0.0, "rates": rates, "passes_80_rule": True}
    vals = list(rates.values())
    delta = max(vals) - min(vals)
    passes = (min(vals) / max(vals) >= 0.8) if max(vals) > 0 else True
    return {"delta": round(delta, 4), "rates": rates, "passes_80_rule": passes}


def equalized_odds_approx(records: list[dict], attr: str) -> float:
    """
    Aproximación de Equalized Odds Δ: diferencia de TPR entre grupos, usando
    true_qual ≥ 0.75 como etiqueta de "realmente calificado".
    """
    groups: dict[str, list[tuple[bool, bool]]] = {}
    for r in records:
        qualified = r["true_qual"] >= 0.75
        advanced = r["decision"] in POSITIVE
        groups.setdefault(str(r[attr]), []).append((qualified, advanced))
    tprs = []
    for pairs in groups.values():
        pos = [adv for q, adv in pairs if q]
        if pos:
            tprs.append(sum(pos) / len(pos))
    return round(max(tprs) - min(tprs), 4) if len(tprs) >= 2 else 0.0


def mean_score_error(records: list[dict], group_filter) -> float:
    """
    Error medio (score asignado − ground-truth) para el subconjunto de records
    que cumple `group_filter`. Negativo = subestimación del grupo.
    """
    errs = [r["score"] - r["true_qual"] for r in records if group_filter(r)]
    return round(float(np.mean(errs)), 4) if errs else 0.0


def treatment_gap(records: list[dict]) -> float:
    """
    Brecha de trato entre grupos de riesgo: |error medio bajo − error medio alto|.
    Captura cuánto más favorablemente se trata a un grupo respecto del otro frente
    a su calificación real.
    """
    low = mean_score_error(records, lambda r: r["bias_risk"] == "low")
    high = mean_score_error(records, lambda r: r["bias_risk"] == "high")
    return round(abs(low - high), 4)
