#!/usr/bin/env python
"""
FPR del Monitor bajo H₀ (B6): ¿cuánto ruido bloquea cada modo del Monitor cuando NO
hay disparidad real (tasas idénticas por grupo)?

Compara el monitor PUNTUAL (|Δ̂| > τ_b, sin garantía) contra el CERTIFICADO
(LCB_δ(|Δ|) > τ_b — Hoeffding, core/stats.py) simulando ventanas H₀. Reporta la tasa
de falsos bloqueos de ambos con IC binomial (Wilson). Es el número que calibra τ_b y
el tamaño de ventana operativo — material directo del capítulo experimental.

La garantía esperada: FPR_certificado ≤ δ (por construcción); el puntual la supera
con ventanas chicas (bloquea ruido — B6 de la auditoría).
"""
from __future__ import annotations
import argparse
import math
import sys

import numpy as np

from moav_hr.core.monitor import FairnessUtilityMonitor


def wilson_ci(hits: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """IC binomial de Wilson para una proporción."""
    if n == 0:
        return (0.0, 1.0)
    p = hits / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def h0_window(rng: np.random.Generator, n_per_group: int, rate: float) -> list[dict]:
    recs = []
    for group in ("A", "B"):
        adv = rng.random(n_per_group) < rate
        recs += [{"origin_group": group, "gender": "F", "true_qual": 0.9,
                  "score": 0.8, "bias_risk": "low",
                  "decision": "ADVANCE" if a else "REJECT"} for a in adv]
    return recs


def main() -> int:
    ap = argparse.ArgumentParser(description="FPR del monitor bajo H0 (B6)")
    ap.add_argument("--sims", type=int, default=2000, help="ventanas H0 simuladas")
    ap.add_argument("--n", type=int, default=200, help="candidatos por grupo y ventana")
    ap.add_argument("--rate", type=float, default=0.5, help="tasa de avance común (H0)")
    ap.add_argument("--tau-b", type=float, default=0.075, help="umbral de bloqueo")
    ap.add_argument("--delta", type=float, default=0.05, help="nivel del certificado")
    ap.add_argument("--seed", type=int, default=20260711)
    args = ap.parse_args()

    mon = FairnessUtilityMonitor(disparity_threshold=args.tau_b)
    rng = np.random.default_rng(args.seed)
    bloqueos_punt = bloqueos_cert = 0
    for _ in range(args.sims):
        recs = h0_window(rng, args.n, args.rate)
        if mon.audit_window(recs).blocked:
            bloqueos_punt += 1
        if mon.audit_window(recs, certified=True, delta=args.delta).blocked:
            bloqueos_cert += 1

    fpr_p, ci_p = bloqueos_punt / args.sims, wilson_ci(bloqueos_punt, args.sims)
    fpr_c, ci_c = bloqueos_cert / args.sims, wilson_ci(bloqueos_cert, args.sims)

    print(f"\n  FPR DEL MONITOR BAJO H₀ (B6) — {args.sims} ventanas, n={args.n}/grupo, "
          f"tasa={args.rate}, τ_b={args.tau_b}, δ={args.delta}")
    print("  " + "─" * 72)
    print(f"  {'modo':<28}{'falsos bloqueos':>16}{'FPR':>8}   IC95 (Wilson)")
    print("  " + "─" * 72)
    print(f"  {'puntual (|Δ̂| > τ_b)':<28}{bloqueos_punt:>16}{fpr_p:>8.4f}   "
          f"[{ci_p[0]:.4f}, {ci_p[1]:.4f}]")
    print(f"  {'certificado (LCB > τ_b)':<28}{bloqueos_cert:>16}{fpr_c:>8.4f}   "
          f"[{ci_c[0]:.4f}, {ci_c[1]:.4f}]")
    print("  " + "─" * 72)
    ok = fpr_c <= args.delta and fpr_p > args.delta
    print(f"  VEREDICTO: certificado {'≤' if fpr_c <= args.delta else '>'} δ "
          f"{'y el puntual lo supera — la garantía hace su trabajo' if ok else '(revisar configuración: con n grande el puntual también puede quedar bajo δ)'}")
    print()
    return 0 if fpr_c <= args.delta else 1


if __name__ == "__main__":
    sys.exit(main())
