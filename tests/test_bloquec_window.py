"""
Bloque C · C6 — bloqueo de VENTANA como dice el paper (camera-ready CACIC 2026, §Monitor):
Ω «bloquea la ventana (suspende la decisión automática sobre ese conjunto de casos) y la
envía a revisión humana». pipeline.escalate_window lo implementa; run_poc.py lo activa
con --window-escalation {point,certified} (default off: el demo no cambia).
"""
import copy

from moav_hr.instances.hr.human_sim import resolve as human_resolve
from moav_hr.instances.hr.pipeline import escalate_window


def _recs():
    return [
        {"origin_group": "AR", "decision": "ADVANCE", "true_qual": 0.90},
        {"origin_group": "AR", "decision": "REJECT", "true_qual": 0.40},
        {"origin_group": "no-AR", "decision": "REJECT", "true_qual": 0.85},
        {"origin_group": "no-AR", "decision": "ESCALATE_HUMAN", "true_qual": 0.70},
    ]


def test_ventana_bloqueada_escala_todo_sin_mutar():
    recs = _recs()
    original = copy.deepcopy(recs)
    out = escalate_window(recs, True)
    assert [r["decision"] for r in out] == ["ESCALATE_HUMAN"] * len(recs)
    assert recs == original                       # la entrada no se muta
    assert all(o is not r for o, r in zip(out, recs))


def test_ventana_no_bloqueada_devuelve_lo_mismo():
    recs = _recs()
    original = copy.deepcopy(recs)
    assert escalate_window(recs, False) == original
    assert recs == original


def test_flujo_b2_con_ventana_bloqueada():
    """Misma lógica que el bloque B2 de run_poc.py, a nivel función (sin CLI)."""
    recs = escalate_window(_recs(), True)
    escalated = [r for r in recs if r["decision"] == "ESCALATE_HUMAN"]
    autos = [r for r in recs if r["decision"] != "ESCALATE_HUMAN"]
    resolved = [dict(r, decision=d) for r, d in
                zip(escalated, human_resolve(escalated, mode="oracle", seed=0,
                                             group_attr="origin_group"))]
    total = autos + resolved
    assert autos == []
    assert total == resolved
    assert len(total) == len(_recs())             # el humano resuelve toda la ventana
    assert all(r["decision"] in ("ADVANCE", "REJECT") for r in total)
