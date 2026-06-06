"""
Ontología de eventos de decisión (JSON-LD).

Justificación (T3.1): se usa una ontología —y no logs planos—
por (1) interoperabilidad semántica con auditores/reguladores sin acuerdo de formato,
(2) razonamiento automático sobre eventos ("¿qué decisiones fueron influidas por el
atributo X?"), y (3) cumplimiento del EU AI Act Art.13 (explicaciones comprensibles
para humanos y sistemas downstream).
"""
from __future__ import annotations
from typing import Any

CONTEXT = {
    "moacv": "https://moav-hr.diit.unlam.edu.ar/ontology/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "eu_ai_act": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj#",
}

# Marcos regulatorios que el audit trail satisface simultáneamente
COMPLIANCE = {
    "eu_ai_act_art12": True,   # logging automático >= 6 meses
    "eu_ai_act_art13": True,   # transparencia / explicaciones
    "eu_ai_act_art14": True,   # supervisión humana
    "nyc_ll144": True,         # bias audit anual
    "ar_disposicion_2_2023": True,
    "ley_25326_art20": True,   # decisiones automatizadas
}


def build_decision_event(state: dict[str, Any]) -> dict[str, Any]:
    """Construye el evento de decisión JSON-LD a partir del estado del pipeline."""
    c = state["candidate"]
    parser = state.get("parser", {})
    matcher = state.get("matcher", {})
    auditor = state.get("auditor", {})
    return {
        "@context": CONTEXT,
        "@type": "moacv:DecisionEvent",
        "trace_id": state["trace_id"],
        "pipeline_version": "MOACV-PoC-v0",
        "candidate_pseudonym": f"CAND-{c.id:04d}",
        "job_id": state["job"]["id"],
        "agent_chain": [
            {
                "agent": "ParserAgent", "layer": "BIO",
                "action": "cv_normalization",
                "sensitive_attrs_detected": parser.get("sensitive", []),
                "sensitive_attrs_retained": [],
            },
            {
                "agent": "SemanticMatcher", "layer": "TBO",
                "action": "semantic_matching",
                "score_output": matcher.get("score"),
                "source": matcher.get("source"),
                "skills_matched": parser.get("skills_matched", []),
            },
            {
                "agent": "BiasAuditor", "layer": "BIO",
                "action": "bias_audit",
                "bias_score": auditor.get("bias_score"),
                "bias_type": auditor.get("bias_type"),
                "threshold": auditor.get("threshold"),
                "decision": "BLOCK" if auditor.get("blocked") else "PASS",
            },
            {
                "agent": "ExplainabilityAgent", "layer": "WIO",
                "action": "explain",
                "explanations": state.get("explain", {}),
            },
        ],
        "final_decision": state["decision"],
        "final_score": auditor.get("adjusted_score"),
        "human_review_required": bool(auditor.get("blocked")),
        "compliance": COMPLIANCE,
    }
