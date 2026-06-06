#!/usr/bin/env python
"""
Demo del pipeline MOACV sobre los 12 candidatos sintéticos.

Por defecto corre en modo 'sim' (determinístico, sin LLM, instantáneo).
Con --mode llm usa Llama 3.1 vía Ollama (inferencia real) — limitá la cantidad
con --limit para no sobrecargar la máquina.

Ejemplos:
    python experiments/run_poc.py                 # MOACV (sim) + caso basal + fairness
    python experiments/run_poc.py --mode llm --limit 3
    python experiments/run_poc.py --langgraph     # corre el DAG sobre LangGraph
    python experiments/run_poc.py --json 3        # imprime el JSON-LD del candidato 3
"""
from __future__ import annotations

import argparse
import json

from moav_hr.synthetic import CANDIDATES, get
from moav_hr.agents.orchestrator import Orchestrator, run_baseline
from moav_hr.fairness.metrics import (demographic_parity, equalized_odds_approx,
                                      mean_score_error, treatment_gap)
from moav_hr.fairness.dag_bias import compute_pipeline_bias_amplification


def origin_group(c) -> str:
    return "AR" if c.origin == "AR" else "no-AR"


def main() -> None:
    ap = argparse.ArgumentParser(description="Demo pipeline MOACV")
    ap.add_argument("--mode", choices=["sim", "llm"], default="sim")
    ap.add_argument("--limit", type=int, default=None, help="máx candidatos (útil en modo llm)")
    ap.add_argument("--langgraph", action="store_true", help="usar el DAG de LangGraph")
    ap.add_argument("--json", type=int, metavar="ID", help="imprimir JSON-LD del candidato ID")
    args = ap.parse_args()

    cands = CANDIDATES[: args.limit] if args.limit else CANDIDATES

    if args.langgraph:
        from moav_hr.pipeline.dag import run_graph
        runner = lambda c: run_graph(c, mode=args.mode)          # noqa: E731
        engine = "LangGraph"
    else:
        orch = Orchestrator(mode=args.mode)
        runner = orch.run_pipeline
        engine = "Orchestrator"

    print(f"\n  MOACV PoC — motor={engine} · modo={args.mode} · {len(cands)} candidatos")
    print("  " + "─" * 92)
    print(f"  {'Candidato':<18}{'Grupo':<8}{'Riesgo':<8}{'tq':>5}{'  basal':>9}{'  MOACV':>9}"
          f"   {'basal→MOACV decisión':<28}")
    print("  " + "─" * 92)

    records, stage_matcher, stage_pipeline, tq_map, grp_map = [], {}, {}, {}, {}
    base_false_rej = moacv_false_rej = 0

    for c in cands:
        st = runner(c)
        base = run_baseline(c)
        a = st["auditor"]
        records.append({
            "gender": c.gender, "origin_group": origin_group(c),
            "decision": st["decision"], "true_qual": c.true_qual,
            "score": a["adjusted_score"], "bias_risk": c.bias_risk,
        })
        stage_matcher[c.id] = st["matcher"]["score"]
        stage_pipeline[c.id] = a["adjusted_score"]
        tq_map[c.id] = c.true_qual
        grp_map[c.id] = origin_group(c)
        if c.true_qual >= 0.75 and base["decision"] == "REJECT":
            base_false_rej += 1
        if c.true_qual >= 0.75 and st["decision"] == "REJECT":
            moacv_false_rej += 1

        arrow = f"{base['decision']:<8}→ {st['decision']}"
        print(f"  {c.name:<18}{('♀ '+c.origin if c.gender=='F' else '♂ '+c.origin):<8}"
              f"{c.bias_risk:<8}{c.true_qual:>5.2f}{base['score']:>9.3f}{a['adjusted_score']:>9.3f}"
              f"   {arrow:<28}")

    print("  " + "─" * 92)

    # ---- fairness ----
    dp_g = demographic_parity(records, "gender")
    dp_o = demographic_parity(records, "origin_group")
    eo = equalized_odds_approx(records, "origin_group")

    high = lambda r: r["bias_risk"] == "high"   # noqa: E731
    print("\n  FAIRNESS (MOACV)")
    print(f"    Demographic Parity Δ  · género      : {dp_g['delta']:.3f}  (80%-rule: {dp_g['passes_80_rule']})")
    print(f"    Demographic Parity Δ  · origen      : {dp_o['delta']:.3f}  (80%-rule: {dp_o['passes_80_rule']})")
    print(f"    Equalized Odds Δ      · origen      : {eo:.3f}")
    print(f"    Subestim. alto riesgo (score−tq)    : {mean_score_error(records, high):.3f}")
    print(f"    Brecha de trato por grupo de riesgo : {treatment_gap(records):.3f}")

    print("\n  CASO BASAL vs MOACV")
    print(f"    Falsos rechazos de candidatos calificados : basal={base_false_rej}  MOACV={moacv_false_rej}")

    # ---- amplificación de sesgo en la cadena ----
    amp = compute_pipeline_bias_amplification(
        [("SemanticMatcher", stage_matcher)], stage_pipeline, tq_map, grp_map)
    print("\n  AMPLIFICACIÓN/ATENUACIÓN DE SESGO EN LA CADENA (Eje 1)")
    print(f"    {amp}")

    if args.json is not None:
        c = get(args.json)
        st = runner(c)
        print(f"\n  EVENTO JSON-LD — {c.name}")
        print(json.dumps(st["trail"].decision_event(st), ensure_ascii=False, indent=2))
    print()


if __name__ == "__main__":
    main()
