"""B4 — topologías de comité: agregación, equivalencia k=1≡cadena, D por miembros."""
import pytest

from moav_hr.core import fairness
from moav_hr.core.committee import Committee, aggregate
from moav_hr.instances.hr.parser_agent import normalize_profile, build_si
from moav_hr.instances.hr.pipeline import HRPipeline
from moav_hr.instances.hr.synthetic import CANDIDATES


def test_agregaciones_en_casos_construidos():
    assert aggregate([0.6, 0.8, 1.0], "mean")["score"] == pytest.approx(0.8)
    assert aggregate([0.6, 0.8, 1.0], "median")["score"] == pytest.approx(0.8)
    maj = aggregate([0.8, 0.8, 0.6], "majority")          # 2/3 votos ≥ 0.75
    assert maj["majority_decision"] == "ADVANCE" and maj["score"] == pytest.approx(0.8)
    assert aggregate([0.6, 0.9, 0.6], "majority")["majority_decision"] == "REJECT"
    with pytest.raises(ValueError):
        aggregate([0.5], "promedio")


def test_k1_equivale_a_la_cadena():
    chain = HRPipeline(mode="sim")
    com = HRPipeline(mode="sim", topology="committee", k=1, aggregation="mean")
    chain.warmup(CANDIDATES)
    com.warmup(CANDIDATES)
    for c in CANDIDATES:
        s_chain = chain.process(c)["matcher"]["score"]
        s_com = com.process(c)["matcher"]["score"]
        assert s_com == pytest.approx(s_chain, abs=1e-9)


def test_miembros_identicos_dan_D_cero():
    pipe = HRPipeline(mode="sim", topology="committee", k=3)
    pipe.warmup(CANDIDATES)                                # misma siembra para los 3
    states = [pipe.process(c) for c in CANDIDATES]
    D = fairness.diversity(pipe.matcher.member_bias_series(states))
    assert D == pytest.approx(0.0, abs=1e-6)


def test_miembros_perturbados_dan_D_positiva():
    pipe = HRPipeline(mode="sim", topology="committee", k=3)
    for i, m in enumerate(pipe.matcher.members):           # siembras DISTINTAS por miembro
        for c in CANDIDATES:
            si = build_si(normalize_profile(c))
            action = "ADVANCE" if (c.id + i) % 2 == 0 else "REJECT"
            m.learn(si, action, {"outcome": action}, success=True, u=0.9)
    states = [pipe.process(c) for c in CANDIDATES]
    D = fairness.diversity(pipe.matcher.member_bias_series(states))
    assert D > 0.0


def test_pipeline_comite_end_to_end():
    pipe = HRPipeline(mode="sim", topology="committee", k=3, aggregation="median")
    pipe.warmup(CANDIDATES)
    st = pipe.process(CANDIDATES[0])
    m = st["matcher"]
    assert len(m["member_scores"]) == 3
    assert m["source"].startswith("committee/median")
    assert st["decision"] in ("ADVANCE", "REJECT", "ESCALATE_HUMAN")
    # el ABox ve a los MIEMBROS como agentes reales
    assert len(pipe.agents) == 3 + 3                       # parser + 3 matchers + auditor + explainer


def test_committee_requiere_miembros_y_agregacion_valida():
    with pytest.raises(ValueError):
        Committee([], "mean")
