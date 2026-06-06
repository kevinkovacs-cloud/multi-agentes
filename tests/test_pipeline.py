"""
Tests del pipeline MOACV (modo sim, determinístico).

Verifican: decisiones por candidato, el caso basal vs MOACV (falsos rechazos
corregidos), el audit trail / ontología, fairness y atenuación de sesgo en la cadena.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from moav_hr.synthetic import CANDIDATES, get
from moav_hr.agents.orchestrator import Orchestrator, run_baseline
from moav_hr.fairness.metrics import demographic_parity, treatment_gap, mean_score_error
from moav_hr.fairness.dag_bias import compute_pipeline_bias_amplification
from moav_hr.audit.ontology import COMPLIANCE


def _origin_group(c):
    return "AR" if c.origin == "AR" else "no-AR"


def test_decisiones_por_candidato():
    orch = Orchestrator(mode="sim")
    dec = {c.id: orch.run_pipeline(c)["decision"] for c in CANDIDATES}
    assert dec[3] == "ESCALATE_HUMAN"    # Fátima (alto riesgo interseccional)
    assert dec[7] == "ESCALATE_HUMAN"    # Priya
    assert dec[10] == "ESCALATE_HUMAN"   # Ahmed
    assert dec[2] == "ADVANCE"           # Carlos (bajo riesgo)
    assert dec[11] == "REJECT"           # Camila (poca exp, no alcanza umbral)


def test_caso_basal_corrige_falso_rechazo():
    # Ahmed: el basal lo rechaza pese a estar calificado; MOACV lo escala a humano.
    ahmed = get(10)
    assert run_baseline(ahmed)["decision"] == "REJECT"
    assert Orchestrator(mode="sim").run_pipeline(ahmed)["decision"] == "ESCALATE_HUMAN"
    # Fátima: el basal la avanza con score subestimado; MOACV detecta el sesgo.
    fatima = get(3)
    assert run_baseline(fatima)["decision"] == "ADVANCE"


def test_audit_trail_y_ontologia():
    st = Orchestrator(mode="sim").run_pipeline(get(3))
    assert len(st["trail"]) >= 6
    event = st["trail"].decision_event(st)
    assert event["@type"] == "moacv:DecisionEvent"
    assert event["final_decision"] == "ESCALATE_HUMAN"
    assert event["human_review_required"] is True
    assert event["compliance"] == COMPLIANCE
    # el Parser detecta atributos sensibles pero NO los retiene (guardrail BIO)
    parser_step = event["agent_chain"][0]
    assert parser_step["sensitive_attrs_retained"] == []
    assert "origin=SY" in parser_step["sensitive_attrs_detected"]


def test_madurez_de_los_agentes():
    orch = Orchestrator(mode="sim")
    assert orch.parser.maturity.value == "mature"
    assert orch.matcher.maturity.value == "trained"
    assert orch.auditor.maturity.value == "mature"
    assert orch.explainer.maturity.value == "novato"


def test_fairness_y_atenuacion():
    orch = Orchestrator(mode="sim")
    records, matcher_scores, pipe_scores, tq, grp = [], {}, {}, {}, {}
    for c in CANDIDATES:
        st = orch.run_pipeline(c)
        a = st["auditor"]
        records.append({"gender": c.gender, "origin_group": _origin_group(c),
                        "decision": st["decision"], "true_qual": c.true_qual,
                        "score": a["adjusted_score"], "bias_risk": c.bias_risk})
        matcher_scores[c.id] = st["matcher"]["score"]
        pipe_scores[c.id] = a["adjusted_score"]
        tq[c.id] = c.true_qual
        grp[c.id] = _origin_group(c)

    dp = demographic_parity(records, "origin_group")
    assert 0.0 <= dp["delta"] <= 1.0
    # MOACV corrige la subestimación del grupo de alto riesgo → ~0
    assert abs(mean_score_error(records, lambda r: r["bias_risk"] == "high")) < 0.01
    # la cadena atenúa el sesgo del matcher (el Bias Auditor lo reduce)
    amp = compute_pipeline_bias_amplification(
        [("matcher", matcher_scores)], pipe_scores, tq, grp)
    assert amp.regime == "attenuation"
    assert amp.pipeline_bias < amp.individual_biases["matcher"]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"OK  {name}")
    print("\nTodos los tests del pipeline pasaron.")
