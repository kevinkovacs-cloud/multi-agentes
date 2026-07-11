"""
Simulador de humano (B2) — resuelve los casos ESCALADOS y habilita μ_total.

El humano simulado SÍ puede ver el ground-truth: es la resolución FINAL del caso
derivado, no una parte del sistema bajo medición. Con él se separan los dos regímenes
que la censura del deferral confunde (B1 de la auditoría):
  · μ_auto : disparidad del flujo AUTOMATIZADO puro (solo casos no derivados);
  · μ_total: disparidad del sistema completo, con las derivaciones resueltas.

Modos:
  · oracle : decide por true_qual ≥ umbral (árbitro perfecto);
  · noisy  : oracle invertido con probabilidad ε (revisor falible);
  · biased : al grupo desfavorecido le exige umbral corrido en b_h — modela que el
    humano del escalamiento NO es un árbitro gratis (la literatura documenta que el
    sesgo de la IA se propaga a los decisores humanos).
"""
from __future__ import annotations

import numpy as np

MODES = ("oracle", "noisy", "biased")


def resolve(records_escalated: list[dict], mode: str = "oracle", seed: int = 0,
            epsilon: float = 0.1, b_h: float = 0.0,
            group_attr: str = "origin_group", disadvantaged: str = "no-AR",
            qual_threshold: float = 0.75) -> list[str]:
    """Devuelve la decisión final ("ADVANCE"/"REJECT") por cada caso escalado."""
    if mode not in MODES:
        raise ValueError(f"mode debe ser uno de {MODES}")
    rng = np.random.default_rng(seed)
    decisions = []
    for r in records_escalated:
        thr = qual_threshold
        if mode == "biased" and str(r[group_attr]) == disadvantaged:
            thr += b_h
        decision = "ADVANCE" if r["true_qual"] >= thr else "REJECT"
        if mode == "noisy" and rng.random() < epsilon:
            decision = "REJECT" if decision == "ADVANCE" else "ADVANCE"
        decisions.append(decision)
    return decisions
