"""
Amplificación/atenuación de sesgo en la cadena de agentes (DAG-MAS).

Extiende la idea de BiasAmp→ (Wang & Russakovsky, ICML 2021) — definida para un
modelo individual — a una cadena de agentes coordinados. Es la infraestructura
empírica del Eje 1 de la tesis (Vacancia 1): medir cuándo la composición de agentes
amplifica vs. atenúa el sesgo individual.

NOTA: en esta PoC el sesgo por agente se calcula sobre scores simulados. La
formalización y los teoremas de composición son trabajo de los Años 2-3.
"""
from __future__ import annotations
from dataclasses import dataclass

import numpy as np


@dataclass
class BiasAmpResult:
    individual_biases: dict[str, float]   # sesgo por agente
    pipeline_bias: float                  # sesgo del pipeline completo
    amplification_factor: float           # pipeline / media(individuales)
    regime: str                           # "amplification" | "attenuation" | "neutral"

    def __str__(self) -> str:
        per = ", ".join(f"{a}={b:.3f}" for a, b in self.individual_biases.items())
        return (f"[{self.regime}] pipeline={self.pipeline_bias:.3f} "
                f"factor={self.amplification_factor:.2f} | por-agente: {per}")


def _group_bias(scores: dict[int, float], true_qual: dict[int, float],
                group: dict[int, str]) -> float:
    """Sesgo de una etapa = brecha entre el error medio del grupo más favorecido
    y el del menos favorecido (error = score − ground-truth)."""
    errs: dict[str, list[float]] = {}
    for cid, s in scores.items():
        errs.setdefault(group[cid], []).append(s - true_qual[cid])
    means = [float(np.mean(v)) for v in errs.values() if v]
    return abs(max(means) - min(means)) if len(means) >= 2 else 0.0


def compute_pipeline_bias_amplification(
    stage_scores: list[tuple[str, dict[int, float]]],
    pipeline_output: dict[int, float],
    true_qual: dict[int, float],
    group: dict[int, str],
) -> BiasAmpResult:
    """
    stage_scores:    sesgos por agente intermedio [(nombre, {candidate_id: score}), ...].
    pipeline_output: scores finales del pipeline {candidate_id: score}.
    true_qual:       {candidate_id: calificación real}.
    group:           {candidate_id: grupo protegido}.

    Compara el sesgo del pipeline completo contra el de sus componentes:
    amplificación si supera al peor agente, atenuación si queda por debajo del mejor.
    """
    individual = {name: round(_group_bias(sc, true_qual, group), 4)
                  for name, sc in stage_scores}
    pipeline_bias = round(_group_bias(pipeline_output, true_qual, group), 4)
    mean_ind = float(np.mean(list(individual.values()))) if individual else 0.0
    factor = round(pipeline_bias / mean_ind, 3) if mean_ind > 0 else 1.0

    max_ind = max(individual.values()) if individual else 0.0
    min_ind = min(individual.values()) if individual else 0.0
    if pipeline_bias > max_ind + 1e-9:
        regime = "amplification"
    elif pipeline_bias < min_ind - 1e-9:
        regime = "attenuation"
    else:
        regime = "neutral"

    return BiasAmpResult(individual, round(pipeline_bias, 4), factor, regime)
