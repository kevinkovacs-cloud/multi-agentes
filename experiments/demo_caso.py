#!/usr/bin/env python
"""
Caso de demostración del PoC (Plan §5) — determinístico y narrado.

Reproduce SIEMPRE igual el caso ilustrativo: un candidato calificado al que el caso
basal (un único agente) RECHAZA por subestimación, y que MOACV deriva a REVISIÓN HUMANA
cuando el Monitor de Utilidad de Equidad detecta sesgo por encima del umbral.

Muestra el flujo de los 5 agentes, el audit trail, el grafo RDF (validado con SHACL)
y una consulta SPARQL.

Uso:  python experiments/demo_caso.py            (default: Ahmed El-Sayed, id 10)
      python experiments/demo_caso.py 3          (Fátima)
"""
from __future__ import annotations
import sys

from moav_hr.instances.hr.synthetic import CANDIDATES, get
from moav_hr.instances.hr.pipeline import HRPipeline, run_baseline
from moav_hr.core.ontology import abox, shapes, queries


def rule(ch="─"):
    print("  " + ch * 74)


def main():
    cid = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    c = get(cid)

    pipe = HRPipeline(mode="sim")            # determinístico, sin LLM
    pipe.warmup(CANDIDATES)                   # siembra la base de teorías (experiencia)

    print(f"\n  CASO DE DEMOSTRACIÓN MOACV — {c.name}")
    rule("═")
    print(f"  Candidato: {c.name}  ·  {c.gender}/{c.origin}/{c.age}a  ·  {c.exp}a exp  ·  {c.edu}")
    print(f"  Skills: {', '.join(c.skills)}")
    print(f"  Calificación real (ground-truth, tq) = {c.true_qual:.2f}   [≥0.75 = calificado]")
    rule()

    # --- CASO BASAL (un único agente) ---
    base = run_baseline(c)
    print(f"\n  [1] CASO BASAL — un único agente LLM (sin auditoría, sin ciclo de vida)")
    print(f"      score = {base['score']:.3f}  →  decisión = {base['decision']}")
    if c.true_qual >= 0.75 and base["decision"] == "REJECT":
        print(f"      ⚠️  FALSO RECHAZO: candidato calificado (tq={c.true_qual:.2f}) rechazado por subestimación.")

    # --- PIPELINE MOACV (5 agentes) ---
    st = pipe.process(c)
    p, m, a, e = st["parser"], st["matcher"], st["auditor"], st["explain"]
    print(f"\n  [2] PIPELINE MOACV — 5 agentes con ciclo de vida")
    print(f"      Parser (BIO, región 1)      → Si={p['si']}")
    print(f"                                    sensibles detectados={p['sensitive']}  retenidos={p['retained']}  (guardrail BIO)")
    print(f"      Matcher (TBO, región 2)     → score={m['score']:.3f}  ({m['source']}, {m['n_retrieved']} teorías RAG)")
    print(f"      Bias Auditor (Ω, región 4)  → sesgo={a['bias_score']:.3f} ({a['bias_type']}) "
          f"umbral={a['threshold']}  {'⛔ BLOQUEA' if a['blocked'] else '✓ OK'}")
    print(f"      Explainability (WIO)        → L3: {e['L3']}")
    print(f"      Orchestrator                → DECISIÓN FINAL = {st['decision']}  (score ajustado={a['adjusted_score']:.3f})")

    # --- CONTRASTE ---
    print(f"\n  [3] CONTRASTE")
    print(f"      basal={base['decision']}   →   MOACV={st['decision']}")
    if base["decision"] == "REJECT" and st["decision"] == "ESCALATE_HUMAN":
        print(f"      ✅ MOACV detecta el sesgo y deriva a revisión humana (EU AI Act Art.14) "
              f"en lugar de rechazar.")

    # --- AUDIT TRAIL + RDF ---
    print(f"\n  [4] AUDIT TRAIL + ONTOLOGÍA RDF (§2.5)")
    print(f"      eventos registrados (trace {st['trace_id']}): {len(st['trail'])}")
    for ev in st["trail"].events:
        reg = f"R{ev.region}" if ev.region else "  "
        print(f"        {reg}  [{ev.agent}] {ev.action}")
    g = abox.build_abox(st, agents=list(pipe.agents))
    conforms, _ = shapes.validate(g)
    esc = queries.run(g, queries.Q_ESCALATIONS)
    print(f"      tripletas RDF generadas: {len(g)}  ·  spans OpenTelemetry: {len(st['trail'].spans())}")
    print(f"      validación SHACL conforme: {conforms}  ·  SPARQL escalamientos: {esc[0]['escalamientos'] if esc else 0}")
    rule("═")
    print()


if __name__ == "__main__":
    main()
