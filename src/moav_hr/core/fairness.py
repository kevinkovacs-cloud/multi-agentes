"""
Métricas de equidad por ventana y de composición en el DAG.

v13 §2bis: Def. 5 (fair(W)=1−|Δ(W)|), Def. 6 (U_op(W)=α·acc+(1−α)·fair),
Def. 10 (amplificación μ(M)=b(M)/b_in), Def. 11 (diversidad D(M)).

NOTA DE HONESTIDAD: la conjetura μ<1 es una HIPÓTESIS a contrastar (Eje 1).
Acá se provee el instrumental de medición; no se asume ningún resultado.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

import numpy as np

POSITIVE = ("ADVANCE", "ESCALATE_HUMAN")   # "en proceso" = no rechazado
CRITERIA = ("demographic_parity", "equalized_odds")


# ---------- disparidad por criterio (Δ) ----------
def _pos_rate(decisions: Iterable[str]) -> float:
    ds = list(decisions)
    return sum(1 for d in ds if d in POSITIVE) / len(ds) if ds else 0.0


def demographic_parity_delta(records: list[dict], attr: str) -> float:
    """Δ de paridad demográfica: diferencia de tasas de avance entre grupos."""
    groups: dict[str, list[str]] = {}
    for r in records:
        groups.setdefault(str(r[attr]), []).append(r["decision"])
    rates = [_pos_rate(ds) for ds in groups.values()]
    return round(max(rates) - min(rates), 4) if len(rates) >= 2 else 0.0


def equalized_odds_components(records: list[dict], attr: str) -> dict:
    """
    Componentes de equalized odds (A7): ΔTPR y ΔFPR entre grupos.

    Etiqueta: true_qual ≥ 0.75 (positivos) / < 0.75 (negativos). Cada componente se
    computa solo si ≥2 grupos tienen casos de esa clase; si no, vale 0.0.
    """
    groups: dict[str, list[tuple[bool, bool]]] = {}
    for r in records:
        groups.setdefault(str(r[attr]), []).append(
            (r["true_qual"] >= 0.75, r["decision"] in POSITIVE))
    tprs, fprs = [], []
    for pairs in groups.values():
        pos = [adv for q, adv in pairs if q]
        neg = [adv for q, adv in pairs if not q]
        if pos:
            tprs.append(sum(pos) / len(pos))
        if neg:
            fprs.append(sum(neg) / len(neg))
    tpr_delta = round(max(tprs) - min(tprs), 4) if len(tprs) >= 2 else 0.0
    fpr_delta = round(max(fprs) - min(fprs), 4) if len(fprs) >= 2 else 0.0
    return {"tpr_delta": tpr_delta, "fpr_delta": fpr_delta}


def equalized_odds_delta(records: list[dict], attr: str) -> float:
    """Δ de equalized odds (A7): max(ΔTPR, ΔFPR) — el criterio completo exige igualdad
    en AMBAS tasas; la versión anterior (solo TPR) subestimaba la disparidad."""
    c = equalized_odds_components(records, attr)
    return max(c["tpr_delta"], c["fpr_delta"])


def disparity(records: list[dict], attr: str, criterion: str) -> float:
    """Δ(W) según el criterio elegido (un solo criterio por experimento, Def. 6 nota)."""
    if criterion == "demographic_parity":
        return demographic_parity_delta(records, attr)
    if criterion == "equalized_odds":
        return equalized_odds_delta(records, attr)
    raise ValueError(f"criterio desconocido: {criterion}")


def disparity_signed(records: list[dict], attr: str, criterion: str,
                     reference_group: str) -> float:
    """
    Disparidad FIRMADA (B3): tasa(referencia) − tasa(resto agrupado).

    Positivo ⇒ el sistema desfavorece al grupo NO-referencia (su tasa es menor);
    negativo ⇒ lo favorece (posible sobrecorrección). El grupo de referencia se pasa
    explícito y debe reportarse junto al valor. Para equalized_odds la tasa es la TPR
    (positivos = true_qual ≥ 0.75).
    """
    ref, rest = [], []
    for r in records:
        (ref if str(r[attr]) == reference_group else rest).append(r)
    if not ref or not rest:
        raise ValueError(f"grupo de referencia '{reference_group}' o resto vacío")

    def _rate(rs: list[dict]) -> float:
        if criterion == "demographic_parity":
            return _pos_rate(r["decision"] for r in rs)
        if criterion == "equalized_odds":
            pos = [r for r in rs if r["true_qual"] >= 0.75]
            return _pos_rate(r["decision"] for r in pos) if pos else 0.0
        raise ValueError(f"criterio desconocido: {criterion}")

    return round(_rate(ref) - _rate(rest), 4)


def is_inversion(delta_in: float, delta_out: float, floor: float) -> bool:
    """
    Detector de INVERSIÓN de signo (B3): el sistema pasó de desfavorecer a un grupo a
    desfavorecer al otro con magnitud material (signos opuestos y |Δ_out| > floor).
    Un μ<1 en valor absoluto puede encubrir una sobrecorrección: esta bandera la expone.
    """
    return (delta_in * delta_out < 0) and abs(delta_out) > floor


# ---------- utilidad por ventana (Def. 5, 6) ----------
def fair_window(records: list[dict], attr: str, criterion: str) -> float:
    """fair(W) = 1 − |Δ(W)|  (Def. 5)."""
    return round(1.0 - abs(disparity(records, attr, criterion)), 4)


def acc_window(records: list[dict]) -> float:
    """acc(W): promedio de aciertos sobre la ventana (decisión coincide con tq≥0.75)."""
    if not records:
        return 0.0
    hits = sum(1 for r in records
               if (r["decision"] in POSITIVE) == (r["true_qual"] >= 0.75))
    return round(hits / len(records), 4)


def u_op(records: list[dict], attr: str, criterion: str, alpha: float = 0.5) -> float:
    """U_op(W) = α·acc(W) + (1−α)·fair(W)  (Def. 6)."""
    return round(alpha * acc_window(records)
                 + (1 - alpha) * fair_window(records, attr, criterion), 4)


def mean_score_error(records: list[dict], group_filter) -> float:
    errs = [r["score"] - r["true_qual"] for r in records if group_filter(r)]
    return round(float(np.mean(errs)), 4) if errs else 0.0


# ---------- composición en el DAG (Def. 10, 11) ----------
@dataclass
class AmplificationResult:
    bias_in: float
    bias_out: float
    mu: float | None          # None en el caso degenerado b_in=0
    regime: str               # amplification | attenuation | neutral | bias_introduced | clean

    def __str__(self) -> str:
        m = f"μ={self.mu:.3f}" if self.mu is not None else "μ=n/d (b_in=0)"
        return f"[{self.regime}] b_in={self.bias_in:.4f} b_out={self.bias_out:.4f} {m}"


def amplification(bias_in: float, bias_out: float) -> AmplificationResult:
    """
    Def. 10 — μ(M) = b(M)/b_in, medido contra la ENTRADA (no contra un componente).
    μ>1 amplifica · μ<1 atenúa · μ=1 neutro. Caso degenerado b_in=0: se reporta b_out.
    """
    if bias_in <= 1e-9:
        regime = "bias_introduced" if bias_out > 1e-9 else "clean"
        return AmplificationResult(round(bias_in, 4), round(bias_out, 4), None, regime)
    mu = bias_out / bias_in
    regime = "amplification" if mu > 1 + 1e-9 else "attenuation" if mu < 1 - 1e-9 else "neutral"
    return AmplificationResult(round(bias_in, 4), round(bias_out, 4), round(mu, 4), regime)


def diversity(agent_bias_vectors: dict[str, list[float]], comparable: bool = True) -> float:
    """
    Def. 11 (corregida, A3) — D(M) = (1 − ρ̄) / 2 ∈ [0, 1], con ρ̄ la correlación media
    de las series de sesgo b(aᵢ) entre pares de agentes. Sin clamp: la fórmula ya cae
    en [0,1] para ρ̄ ∈ [−1, 1] (D=0 clones · D=½ independientes · D=1 anticorrelados).

    `comparable=True` DECLARA que las series comparadas provienen de agentes que estiman
    la MISMA cantidad (p. ej., miembros de un comité sobre los mismos candidatos, N2).
    Comparar una etapa con el pipeline que la contiene está estructuralmente
    correlacionado y no mide diversidad — la validación dura es responsabilidad del
    caller; este parámetro deja la precondición explícita.

    Pares con serie constante (var≈0) aportan correlación 0 (sin información).
    Requiere ≥2 vectores (ValueError si no).
    """
    if not comparable:
        raise ValueError("diversity exige series comparables (misma cantidad estimada)")
    names = list(agent_bias_vectors)
    if len(names) < 2:
        raise ValueError("diversity requiere ≥2 series de sesgo (una por agente)")
    corrs = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            vi = np.asarray(agent_bias_vectors[names[i]], dtype=float)
            vj = np.asarray(agent_bias_vectors[names[j]], dtype=float)
            if vi.std() < 1e-9 or vj.std() < 1e-9:
                corrs.append(0.0)
            else:
                corrs.append(float(np.corrcoef(vi, vj)[0, 1]))
    mean_corr = float(np.mean(corrs))
    return round((1.0 - mean_corr) / 2.0, 4)


def d_max(k: int) -> float:
    """
    Cota de alcanzabilidad de la diversidad (A3): D ≤ k / (2(k−1)).

    Toda matriz de correlación válida R de k agentes es PSD ⇒ 1ᵀR1 ≥ 0 ⇒
    ρ̄ ≥ −1/(k−1) ⇒ D = (1−ρ̄)/2 ≤ k/(2(k−1)). El umbral D₀ de la condición C2 no
    puede exigirse por encima de esta cota (k=2 → 1 · k=3 → 0.75 · k→∞ → ½).
    """
    if k < 2:
        raise ValueError("d_max requiere k ≥ 2 agentes")
    return k / (2 * (k - 1))
