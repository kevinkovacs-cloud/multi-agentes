#!/usr/bin/env python
"""
Demo del modelo alineado a la propuesta v13.

Por defecto en modo 'sim' (determinístico, sin LLM). Recorre: warmup de teorías →
pipeline de 5 agentes → auditoría por ventana del Monitor Ω (Def. 5/6, región 4) →
caso basal vs modelo → amplificación μ (Def. 10) y diversidad D (Def. 11) →
ontología RDF + SHACL + SPARQL (§2.5) → fidelidad de teorías (Eje 3) →
compartición coop/colab (Def. 7/8/9, ponderada por Ω).

Uso:
    python experiments/run_poc.py
    python experiments/run_poc.py --mode llm --limit 3
    python experiments/run_poc.py --turtle 3     # imprime el RDF/Turtle del candidato 3
"""
from __future__ import annotations
import argparse

from moav_hr.instances.hr.synthetic import CANDIDATES, get
from moav_hr.instances.hr.pipeline import HRPipeline, run_baseline, record_of, matcher_view
from moav_hr.instances.hr.fidelity import measure_fidelity
from moav_hr.core import fairness
from moav_hr.core.ontology import abox, shapes, queries
from moav_hr.instances.hr.semantic_matcher import SemanticMatcherAgent
from moav_hr.core.sharing import ShareReport  # noqa: F401


def main() -> None:
    ap = argparse.ArgumentParser(description="Demo PoC (v13)")
    ap.add_argument("--mode", choices=["sim", "llm"], default="sim")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--criterion", choices=list(fairness.CRITERIA), default="demographic_parity")
    ap.add_argument("--attr", default="origin_group")
    ap.add_argument("--turtle", type=int, metavar="ID", help="imprime el RDF/Turtle del candidato ID")
    args = ap.parse_args()

    cands = CANDIDATES[: args.limit] if args.limit else CANDIDATES
    pipe = HRPipeline(mode=args.mode, criterion=args.criterion, attr=args.attr)
    n_theories = pipe.warmup(cands)   # región 5: siembra de teorías

    print(f"\n  PoC (v13) · modo={args.mode} · {len(cands)} candidatos · "
          f"teorías sembradas={n_theories}")
    print("  " + "─" * 96)
    print(f"  {'Candidato':<18}{'Grupo':<8}{'Riesgo':<7}{'tq':>5}{'  basal':>9}{'  modelo':>9}"
          f"{'  teorías':>9}   decisión")
    print("  " + "─" * 96)

    moacv_recs, base_recs, states = [], [], []
    base_false_rej = moacv_false_rej = 0
    for c in cands:
        st = pipe.process(c)
        states.append(st)
        b = run_baseline(c)
        a = st["auditor"]
        moacv_recs.append(record_of(st))
        base_recs.append({"gender": c.gender, "origin_group": c.origin_group,
                          "decision": b["decision"], "true_qual": c.true_qual,
                          "score": b["score"], "bias_risk": c.bias_risk})
        base_false_rej += (c.true_qual >= 0.75 and b["decision"] == "REJECT")
        moacv_false_rej += (c.true_qual >= 0.75 and st["decision"] == "REJECT")
        print(f"  {c.name:<18}{('♀ '+c.origin if c.gender=='F' else '♂ '+c.origin):<8}"
              f"{c.bias_risk:<7}{c.true_qual:>5.2f}{b['score']:>9.3f}{a['adjusted_score']:>9.3f}"
              f"{st['matcher']['n_retrieved']:>9}   {b['decision']}→{st['decision']}")
    print("  " + "─" * 96)

    # el Monitor Ω audita la ventana global (región 4)
    audit = pipe.monitor.audit_window(moacv_recs)
    fair_w = audit.fair
    # N3: reputación POR AGENTE — cada decisor acumula fair(W) sobre SUS PROPIAS
    # salidas, en subventanas (3 de 4: historia mínima m0 del donante, A9). El matcher
    # se evalúa por las decisiones que implican sus scores; el auditor, por las finales.
    # Parser/Explainer son transformadores: sin reputación propia (queda el prior r0;
    # la variante 1−d̂_TV vive detrás de pipe.heterogeneous_reputation, default off).
    W_SUB = max(1, len(moacv_recs) // 3)
    for i in range(0, len(moacv_recs), W_SUB):
        chunk = moacv_recs[i:i + W_SUB]
        pipe.matcher.record_window_fairness(
            fairness.fair_window(matcher_view(chunk), args.attr, args.criterion))
        pipe.auditor.record_window_fairness(
            fairness.fair_window(chunk, args.attr, args.criterion))

    # --- fairness por ventana (Def. 5, 6) — auditada por el Monitor Ω ---
    print("\n  FAIRNESS POR VENTANA (MODELO) — auditoría del Monitor Ω (región 4)")
    print(f"    Demographic Parity Δ ({args.attr})     : {fairness.demographic_parity_delta(moacv_recs, args.attr):.3f}")
    print(f"    Equalized Odds Δ ({args.attr})         : {fairness.equalized_odds_delta(moacv_recs, args.attr):.3f}")
    print(f"    fair(W) = 1−|Δ(W)|  [{args.criterion}]  : {audit.fair:.3f}")
    print(f"    acc(W)                                 : {audit.acc:.3f}")
    print(f"    U_op(W) = α·acc+(1−α)·fair             : {audit.u_op:.3f}")
    print(f"    Ventana marcada por Ω (|Δ|>{pipe.monitor.disparity_threshold})     : {audit.blocked}")
    print(f"    Subestim. alto riesgo (score−tq)       : {fairness.mean_score_error(moacv_recs, lambda r: r['bias_risk']=='high'):.3f}")

    # --- caso basal vs modelo ---
    gap_base = abs(fairness.mean_score_error(base_recs, lambda r: r['bias_risk']=='low')
                   - fairness.mean_score_error(base_recs, lambda r: r['bias_risk']=='high'))
    gap_moacv = abs(fairness.mean_score_error(moacv_recs, lambda r: r['bias_risk']=='low')
                    - fairness.mean_score_error(moacv_recs, lambda r: r['bias_risk']=='high'))
    print("\n  CASO BASAL vs MODELO")
    print(f"    Falsos rechazos de calificados : basal={base_false_rej} → modelo={moacv_false_rej}")
    print(f"    Brecha de trato por grupo      : basal={gap_base:.3f} → modelo={gap_moacv:.3f}")

    # --- amplificación relativa al basal (N1: esto es μ_rel, NO el μ de la Def. 10) ---
    amp_gap = fairness.amplification(gap_base, gap_moacv)
    amp_dp = fairness.amplification(
        abs(fairness.disparity(base_recs, args.attr, args.criterion)),
        abs(fairness.disparity(moacv_recs, args.attr, args.criterion)))
    # N2: la D entre "matcher" y "pipeline" se eliminó — una etapa y el pipeline que la
    # contiene están estructuralmente correlacionados y esa comparación no mide
    # diversidad. D se computa SOLO entre miembros de un comité (topology="committee").
    print("\n  COMPOSICIÓN DE SESGO EN LA CADENA (Eje 1 — instrumental, NO valida la conjetura)")
    print(f"    μ_rel por brecha-vs-ground-truth : {amp_gap}")
    print(f"    μ_rel por {args.criterion:<19}: {amp_dp}")
    print("    μ_rel = b(modelo)/b(basal); el μ de la Def. 10 se computa contra la")
    print("    ENTRADA (b_in del benchmark, Eje 2 — fairness.bias_in_reference).")

    # --- ontología RDF + SHACL + SPARQL (§2.5), sobre el lote completo ---
    g = abox.build_abox(states[0], agents=list(pipe.agents))
    for st in states[1:]:
        g += abox.build_abox(st, agents=list(pipe.agents))
    conforms, _ = shapes.validate(g)
    esc = queries.run(g, queries.Q_ESCALATIONS)
    spans = sum(len(st["trail"].spans()) for st in states)
    print("\n  ONTOLOGÍA / AUDIT TRAIL RDF (§2.5)")
    print(f"    Tripletas RDF generadas (lote completo): {len(g)}")
    print(f"    Spans OpenTelemetry capturados         : {spans}")
    print(f"    Validación SHACL conforme              : {conforms}")
    print(f"    SPARQL escalamientos en el grafo       : {esc[0]['escalamientos'] if esc else 0}")

    # --- fidelidad de teorías (Eje 3) ---
    fid = measure_fidelity(pipe, cands)
    print("\n  FIDELIDAD DE TEORÍAS (Eje 3 — dependencia causal de la decisión)")
    print(f"    {fid}")

    # --- compartición (Def. 7/8) ponderada por el Monitor Ω (Def. 9) + gate de evolución (región 7) ---
    print("\n  COMPARTICIÓN DE CONOCIMIENTO (Def. 7/8/9) — ponderada por el Monitor Ω")
    ok_share = pipe.monitor.approve_sharing(pipe.matcher)
    print(f"    Aprobación de Ω para compartir (r≥τ)      : {ok_share} "
          f"(r={pipe.matcher.reputation():.3f}, τ={pipe.monitor.tau})")
    novato = SemanticMatcherAgent(pipe.backend)          # Born (sin entrenar)
    novato.tbo.training_runs = 0
    rep_collab = pipe.matcher.transfer_to(novato, tau=pipe.monitor.tau)
    print(f"    Colaboración matcher(Trained)→novato(Born): {rep_collab.op} aceptada={rep_collab.accepted} "
          f"(refuerza={rep_collab.reinforced}, debilita={rep_collab.weakened}, nuevas={rep_collab.transferred})")
    peer = SemanticMatcherAgent(pipe.backend)            # Trained (mismo estado)
    # el peer debe tener historia PROPIA para donar (A9): procesa el lote y acumula
    # sus subventanas igual que el matcher principal (N3)
    pipe2 = HRPipeline(mode=args.mode); pipe2.warmup(cands)
    recs2 = [record_of(pipe2.process(c)) for c in cands]
    for i in range(0, len(recs2), W_SUB):
        pipe2.matcher.record_window_fairness(
            fairness.fair_window(matcher_view(recs2[i:i + W_SUB]), args.attr, args.criterion))
    rep_coop = pipe.matcher.cooperate_with(pipe2.matcher, tau=pipe.monitor.tau)
    print(f"    Cooperación matcher↔matcher (Trained)     : {rep_coop.op} aceptada={rep_coop.accepted} "
          f"(refuerza={rep_coop.reinforced}, debilita={rep_coop.weakened}, nuevas={rep_coop.transferred})")
    ok_evol = pipe.monitor.gate_evolution(pipe.matcher)
    print(f"    Gate de evolución de Ω (región 7)         : {ok_evol} "
          f"(el matcher {'puede' if ok_evol else 'NO puede'} progresar de estado)")

    if args.turtle is not None:
        st = pipe.process(get(args.turtle))
        print(f"\n  RDF/Turtle — {get(args.turtle).name}\n")
        print(abox.to_turtle(st, agents=list(pipe.agents)))
    print()


if __name__ == "__main__":
    main()
