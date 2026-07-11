#!/usr/bin/env python
"""
E0 — VALIDACIÓN DEL INSTRUMENTO (B5). El GATE de todo el Eje 1: si el harness no
recupera valores de μ, c_k e ι_k CONOCIDOS por diseño, se arregla el instrumento
antes de medir nada con LLMs. Sin LLM: etapas-juguete con parámetros programados.

Diseño:
  · lotes con disparidad de entrada EXACTA (conteos enteros por grupo);
  · etapas sintéticas que realizan b_out = c·b_in + ι sobre las tasas por grupo;
  · (i) modo determinístico: μ end-to-end recuperado == μ de diseño (tol. 1e-6);
  · (ii) c_k por perturbación de b_in e ι_k con entrada balanceada (tol. 1e-6);
  · (iii) modo estocástico: el IC BCa de log μ (remuestreo por LOTES,
    core/stats.bootstrap_bca_log_mu) cubre el verdadero ≥ 90% de las réplicas.

Salida: tabla diseño-vs-recuperado y PASS/FAIL con tolerancias predeclaradas.
Exit code 0 = PASS. Este script es un entregable científico: si falla, se arregla
el instrumento, no el script.
"""
from __future__ import annotations
import argparse
import sys

import numpy as np

from moav_hr.core import stats

BASE_RATE = 0.5           # tasa media de avance (las tasas por grupo son p ± b/2)
TOL_DET = 1e-6            # tolerancia del modo determinístico (predeclarada)
COVERAGE_MIN = 0.90       # cobertura mínima del IC 95% (predeclarada)


# ---------- generador y etapas-juguete ----------

def exact_counts(n_per_group: int, b: float) -> tuple[int, int]:
    """Positivos por grupo que REALIZAN exactamente la disparidad b (conteos enteros)."""
    pos_a = (BASE_RATE + b / 2) * n_per_group
    pos_b = (BASE_RATE - b / 2) * n_per_group
    if abs(pos_a - round(pos_a)) > 1e-9 or abs(pos_b - round(pos_b)) > 1e-9:
        raise ValueError(f"b={b} no es realizable con n={n_per_group} (conteos no enteros)")
    return int(round(pos_a)), int(round(pos_b))


def measured_disparity(pos_a: int, pos_b: int, n: int) -> float:
    return abs(pos_a / n - pos_b / n)


def toy_stage(b_in: float, c: float, iota: float) -> float:
    """Etapa-juguete: transforma la disparidad según b_out = c·b_in + ι (exacto)."""
    return c * b_in + iota


def run_chain_deterministic(b0: float, stages: list[tuple[float, float]],
                            n: int) -> tuple[float, float]:
    """Corre la cadena sobre conteos exactos; devuelve (b̂_in, b̂_out) MEDIDOS."""
    pos_a, pos_b = exact_counts(n, b0)
    b_hat_in = measured_disparity(pos_a, pos_b, n)
    b = b0
    for c, iota in stages:
        b = toy_stage(b, c, iota)
        pos_a, pos_b = exact_counts(n, b)          # la etapa REALIZA su salida
    return b_hat_in, measured_disparity(pos_a, pos_b, n)


def estimate_c(stage: tuple[float, float], b1: float, b2: float, n: int) -> float:
    """ĉ por perturbación de la entrada: (b_out(b2) − b_out(b1)) / (b2 − b1)."""
    c, iota = stage
    outs = []
    for b in (b1, b2):
        pa, pb = exact_counts(n, toy_stage(b, c, iota))
        outs.append(measured_disparity(pa, pb, n))
    return (outs[1] - outs[0]) / (b2 - b1)


def estimate_iota(stage: tuple[float, float], n: int) -> float:
    """ι̂ con entrada BALANCEADA (b_in = 0): la salida es la inyección pura."""
    c, iota = stage
    pa, pb = exact_counts(n, toy_stage(0.0, c, iota))
    return measured_disparity(pa, pb, n)


# ---------- modo estocástico (cobertura del IC de log μ) ----------

def sample_lote(rng: np.random.Generator, n: int, b: float) -> float:
    """Disparidad MEDIDA de un lote muestreado con tasas verdaderas p ± b/2."""
    adv_a = rng.random(n) < (BASE_RATE + b / 2)
    adv_b = rng.random(n) < (BASE_RATE - b / 2)
    return abs(adv_a.mean() - adv_b.mean())


def coverage_experiment(rng: np.random.Generator, b0: float, b_out_true: float,
                        n: int, lotes: int, replicas: int, n_boot: int) -> float:
    log_mu_true = np.log(b_out_true / b0)
    hits = 0
    for _ in range(replicas):
        b_in_lotes = [sample_lote(rng, n, b0) for _ in range(lotes)]
        b_out_lotes = [sample_lote(rng, n, b_out_true) for _ in range(lotes)]
        _, (lo, hi) = stats.bootstrap_bca_log_mu(
            b_in_lotes, b_out_lotes, n_boot=n_boot,
            seed=int(rng.integers(0, 2**31)))
        hits += (lo <= log_mu_true <= hi)
    return hits / replicas


# ---------- main ----------

def main() -> int:
    ap = argparse.ArgumentParser(description="E0 — validación del instrumento (B5)")
    ap.add_argument("--n", type=int, default=2000, help="candidatos por grupo y lote")
    ap.add_argument("--lotes", type=int, default=25)
    ap.add_argument("--replicas", type=int, default=200)
    ap.add_argument("--n-boot", type=int, default=999)
    ap.add_argument("--seed", type=int, default=20260711)
    args = ap.parse_args()

    # diseño (valores elegidos para conteos enteros con n=2000)
    b0 = 0.10
    stages = [(0.5, 0.02), (0.5, 0.03)]         # (c, ι) por etapa
    b1 = toy_stage(b0, *stages[0])              # 0.07
    b2 = toy_stage(b1, *stages[1])              # 0.065
    mu_true = b2 / b0                           # 0.65

    checks: list[tuple[str, float, float, float, bool]] = []

    # (i) μ end-to-end determinístico
    bi, bo = run_chain_deterministic(b0, stages, args.n)
    mu_hat = bo / bi
    checks.append(("μ end-to-end (determinístico)", mu_true, mu_hat,
                   TOL_DET, abs(mu_hat - mu_true) <= TOL_DET))

    # (ii) c_k e ι_k por etapa
    for k, stage in enumerate(stages, start=1):
        c_hat = estimate_c(stage, 0.06, 0.10, args.n)
        checks.append((f"c_{k} (perturbación de b_in)", stage[0], c_hat,
                       TOL_DET, abs(c_hat - stage[0]) <= TOL_DET))
        iota_hat = estimate_iota(stage, args.n)
        checks.append((f"ι_{k} (entrada balanceada)", stage[1], iota_hat,
                       TOL_DET, abs(iota_hat - stage[1]) <= TOL_DET))

    # (iii) cobertura del IC BCa de log μ
    rng = np.random.default_rng(args.seed)
    cov = coverage_experiment(rng, b0, b2, args.n, args.lotes,
                              args.replicas, args.n_boot)
    checks.append((f"cobertura IC95 log μ ({args.replicas} réplicas)",
                   0.95, cov, COVERAGE_MIN, cov >= COVERAGE_MIN))

    # tabla y veredicto
    print("\n  E0 — VALIDACIÓN DEL INSTRUMENTO (agentes-juguete, sin LLM)")
    print("  " + "─" * 76)
    print(f"  {'chequeo':<42}{'diseño':>9}{'recuperado':>12}{'tol/min':>9}  estado")
    print("  " + "─" * 76)
    ok = True
    for name, design, got, tol, passed in checks:
        ok &= passed
        print(f"  {name:<42}{design:>9.4f}{got:>12.6f}{tol:>9.0e}  "
              f"{'PASS' if passed else 'FAIL'}")
    print("  " + "─" * 76)
    print(f"  VEREDICTO: {'PASS — el instrumento recupera los valores de diseño' if ok else 'FAIL — ARREGLAR EL INSTRUMENTO antes de medir con LLMs'}")
    print()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
