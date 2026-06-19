"""Tests del pipeline HR: decisiones, caso basal, madurez, RAG y fidelidad."""
from moav_hr.instances.hr.synthetic import CANDIDATES, get
from moav_hr.instances.hr.pipeline import HRPipeline, run_baseline
from moav_hr.instances.hr.fidelity import measure_fidelity


def _pipe():
    p = HRPipeline(mode="sim")
    p.warmup(CANDIDATES)
    return p


def test_decisiones_por_candidato():
    p = _pipe()
    dec = {c.id: p.process(c)["decision"] for c in CANDIDATES}
    assert dec[3] == "ESCALATE_HUMAN"     # Fátima (sesgo arrastra su score < umbral → revisión humana)
    assert dec[10] == "ESCALATE_HUMAN"    # Ahmed (falso rechazo del basal corregido a escalamiento)
    assert dec[2] == "ADVANCE"            # Carlos (bajo riesgo)
    assert dec[11] == "REJECT"            # Camila (no alcanza el umbral)
    # Priya (alto riesgo pero tq=0.88): la experiencia recuperada acerca su score a su
    # calificación real, por lo que el auditor no necesita escalarla → avanza (RAG en acción).
    assert dec[7] == "ADVANCE"


def test_caso_basal_corrige_falso_rechazo():
    assert run_baseline(get(10))["decision"] == "REJECT"
    assert _pipe().process(get(10))["decision"] == "ESCALATE_HUMAN"


def test_madurez_de_los_agentes():
    p = _pipe()
    assert p.parser.maturity.label == "mature"
    assert p.matcher.maturity.label == "trained"
    assert p.auditor.maturity.label == "mature"
    assert p.explainer.maturity.label == "novato"


def test_rag_recupera_teorias_y_condiciona():
    st = _pipe().process(get(1))
    assert st["matcher"]["n_retrieved"] >= 1          # recupera teorías sembradas (§2.2)
    assert st["matcher"]["source"] == "sim+theory"     # la teoría entra en la decisión


def test_fidelidad_harness():
    fid = measure_fidelity(_pipe(), CANDIDATES)
    assert fid.n == len(CANDIDATES)
    assert fid.score_dependence > 0.0   # la decisión depende causalmente de las teorías
