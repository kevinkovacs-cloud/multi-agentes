"""
Harness de fidelidad de teorías (v13 §2bis.5, Eje 3 — motivado por Zhao et al. 2026).

Mide la dependencia causal de la decisión respecto de las teorías recuperadas mediante
intervención: se compara la decisión del matcher con (a) las teorías reales, (b) ablacionadas
(sin teorías) y (c) permutadas (acción invertida). Reporta qué fracción de las decisiones
depende causalmente de la experiencia recuperada.

HONESTIDAD: no se fabrica ningún resultado; el harness reporta la dependencia medida tal cual.
"""
from __future__ import annotations
from dataclasses import dataclass

from moav_hr.core.theory import Theory
from moav_hr.instances.hr.parser_agent import normalize_profile, build_si


@dataclass
class FidelityReport:
    n: int
    n_with_theories: int
    score_dependence: float       # frac. con score distinto al ablacionar
    decision_dependence: float    # frac. con decisión que cambia al ablacionar
    permute_decision_dependence: float

    def __str__(self) -> str:
        return (f"fidelidad: n={self.n} (con teorías={self.n_with_theories}) · "
                f"dep_score={self.score_dependence:.2f} · dep_decisión={self.decision_dependence:.2f} · "
                f"dep_decisión(permutado)={self.permute_decision_dependence:.2f}")


def _invert(t: Theory) -> Theory:
    return Theory(si=t.si, a=("REJECT" if t.a == "ADVANCE" else "ADVANCE"),
                  sf=t.sf, p=t.p, k=t.k, u=t.u)


def measure_fidelity(pipeline, candidates, decision_threshold: float = 0.75) -> FidelityReport:
    m = pipeline.matcher
    n = with_th = score_dep = dec_dep = perm_dep = 0
    for c in candidates:
        si = build_si(normalize_profile(c))
        retrieved = m.retrieve(si)
        s_real, _ = m._score_sim(c, retrieved)
        s_abl, _ = m._score_sim(c, [])
        s_perm, _ = m._score_sim(c, [_invert(t) for t in retrieved])
        n += 1
        if retrieved:
            with_th += 1
        if abs(s_real - s_abl) > 1e-9:
            score_dep += 1
        if (s_real >= decision_threshold) != (s_abl >= decision_threshold):
            dec_dep += 1
        if (s_real >= decision_threshold) != (s_perm >= decision_threshold):
            perm_dep += 1
    return FidelityReport(
        n=n, n_with_theories=with_th,
        score_dependence=round(score_dep / n, 3) if n else 0.0,
        decision_dependence=round(dec_dep / n, 3) if n else 0.0,
        permute_decision_dependence=round(perm_dep / n, 3) if n else 0.0,
    )
