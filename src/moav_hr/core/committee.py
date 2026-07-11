"""
Topologías de COMITÉ (B4) — k agentes puntúan el MISMO caso y se agrega.

Es la topología donde la condición C2 (diversidad) tiene canal causal: en la cadena
secuencial hay UN solo decisor de score y "descorrelacionar sesgos" no tiene sobre qué
actuar (ataque del canal ausente — auditoría §3.1). El comité expone los scores
individuales de sus miembros: las series de sesgo POR MIEMBRO son las que alimentan
D = (1−ρ̄)/2 (Def. 11) de forma comparable (N2).

Genérico: los miembros son MOACVAgents (cada uno con su base de teorías propia) que
escriben state["matcher"]; el comité los ejecuta secuencialmente sobre copias del
estado y agrega. Agregaciones: mean · median · majority (voto sobre la decisión
umbralizada; como score de continuidad para el pipeline se expone la mediana —
elección simple documentada, presupuesto de sanidad del handoff).
"""
from __future__ import annotations
import statistics
from typing import Optional

from moav_hr.core.agent import MOACVAgent

AGGREGATIONS = ("mean", "median", "majority")


def aggregate(scores: list[float], aggregation: str,
              decision_threshold: float = 0.75) -> dict:
    """Agrega scores de miembros → {"score": float, "majority_decision": str|None}."""
    if aggregation not in AGGREGATIONS:
        raise ValueError(f"aggregation debe ser una de {AGGREGATIONS}")
    if not scores:
        raise ValueError("sin scores de miembros")
    if aggregation == "mean":
        return {"score": round(sum(scores) / len(scores), 3), "majority_decision": None}
    if aggregation == "median":
        return {"score": round(statistics.median(scores), 3), "majority_decision": None}
    votes = sum(1 for s in scores if s >= decision_threshold)
    decision = "ADVANCE" if votes * 2 > len(scores) else "REJECT"
    return {"score": round(statistics.median(scores), 3), "majority_decision": decision}


class Committee:
    """Comité de k miembros para un rol decisor (ocupa el lugar del Matcher en HR)."""

    def __init__(self, members: list[MOACVAgent], aggregation: str = "mean",
                 decision_threshold: float = 0.75):
        if not members:
            raise ValueError("el comité requiere ≥1 miembro")
        if aggregation not in AGGREGATIONS:
            raise ValueError(f"aggregation debe ser una de {AGGREGATIONS}")
        self.members = members
        self.aggregation = aggregation
        self.decision_threshold = decision_threshold
        self.name = f"Committee(k={len(members)},{aggregation})"
        self.role = members[0].role

    def run(self, state: dict) -> dict:
        outs = []
        for m in self.members:
            st = dict(state)              # copia superficial: cada miembro decide solo
            m.run(st)
            outs.append(st["matcher"])
        scores = [o["score"] for o in outs]
        agg = aggregate(scores, self.aggregation, self.decision_threshold)
        state["matcher"] = {
            "score": agg["score"],
            "source": f"committee/{self.aggregation}(k={len(self.members)})",
            "n_retrieved": max(o["n_retrieved"] for o in outs),
            "member_scores": scores,                      # series de sesgo por miembro → D
            "members": [m.name for m in self.members],
            "majority_decision": agg["majority_decision"],
            "si": outs[0]["si"],
        }
        state["trail"].record(self.name, "TBO", "committee_matching", region=2,
                              k=len(self.members), aggregation=self.aggregation,
                              score=agg["score"])
        return state

    # reputación (Def. 9/N3): cada miembro acumula su propia historia
    def record_window_fairness(self, fair_w: float) -> None:
        for m in self.members:
            m.record_window_fairness(fair_w)

    def member_bias_series(self, states: list[dict],
                           truth_key: Optional[str] = None) -> dict[str, list[float]]:
        """
        Series de sesgo POR MIEMBRO (evaluación, puede usar ground-truth del harness):
        b_i[c] = score_i(c) − true_qual(c). Insumo de fairness.diversity (N2).
        """
        series: dict[str, list[float]] = {m.name + f"#{i}": []
                                          for i, m in enumerate(self.members)}
        for st in states:
            tq = st["candidate"].true_qual
            for i, s in enumerate(st["matcher"]["member_scores"]):
                series[self.members[i].name + f"#{i}"].append(s - tq)
        return series
