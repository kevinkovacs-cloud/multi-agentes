"""
B1 — auditor experimental sin oráculo: (i) no accede a variables del generador
(verificado con candidato-centinela); (ii) corre end-to-end en el pipeline.
"""
import pytest

from moav_hr.core.audit.trail import AuditTrail
from moav_hr.instances.hr.bias_auditor_exp import (ExperimentalBiasAuditor,
                                                   observable_view)
from moav_hr.instances.hr.pipeline import HRPipeline
from moav_hr.instances.hr.synthetic import CANDIDATES, get


class SpyCandidate:
    """Proxy que registra TODOS los atributos accedidos del candidato real."""

    def __init__(self, real):
        object.__setattr__(self, "_real", real)
        object.__setattr__(self, "accessed", set())

    def __getattr__(self, name):
        self.accessed.add(name)
        return getattr(self._real, name)


def _estado(spy) -> dict:
    return {"candidate": spy,
            "matcher": {"score": 0.82},
            "parser": {"si": {"skills_match": 3, "exp_band": "mid"}},
            "trail": AuditTrail("TRC-TEST")}


def test_el_auditor_no_lee_variables_del_generador():
    spy = SpyCandidate(get(3))                       # Fátima, con bias_risk/true_qual
    auditor = ExperimentalBiasAuditor()
    auditor.run(_estado(spy))
    prohibidas = {"bias_risk", "true_qual", "match_score"}
    assert not (spy.accessed & prohibidas), f"accedió a {spy.accessed & prohibidas}"
    # y sí usa lo permitido (protegidos para agregación por ventana)
    assert {"origin_group", "gender"} <= spy.accessed


def test_observable_view_solo_expone_lo_permitido():
    view = observable_view(_estado(SpyCandidate(get(3))))
    assert set(view) == {"score", "si", "origin_group", "gender"}


def test_nunca_ajusta_el_score():
    spy = SpyCandidate(get(3))
    st = _estado(spy)
    ExperimentalBiasAuditor().run(st)
    assert st["auditor"]["adjusted_score"] == st["matcher"]["score"]
    assert st["auditor"]["blocked"] is False         # el bloqueo es de ventana


def test_end_to_end_pipeline_experimental():
    pipe = HRPipeline(mode="sim", auditor_mode="exp")
    pipe.warmup(CANDIDATES)
    for c in CANDIDATES:
        st = pipe.process(c)
        # en modo exp la decisión final es puro umbral del matcher (nunca ESCALATE)
        assert st["decision"] in ("ADVANCE", "REJECT")
        assert st["auditor"]["adjusted_score"] == st["matcher"]["score"]
    audit = pipe.auditor.close_window(delta=0.05)
    assert audit.n == len(CANDIDATES)
    assert audit.lcb >= 0.0 and audit.delta == 0.05
    assert pipe.auditor.close_window() is None       # la ventana quedó vaciada


def test_certificado_de_ventana_exige_dos_grupos():
    auditor = ExperimentalBiasAuditor()
    auditor.run(_estado(SpyCandidate(get(1))))       # un solo grupo (AR)
    with pytest.raises(ValueError):
        auditor.close_window()
