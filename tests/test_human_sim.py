"""B2 — simulador de humano: oracle / noisy / biased y su efecto en μ_total."""
import pytest

from moav_hr.instances.hr.human_sim import resolve


def _esc(group: str, tq: float) -> dict:
    return {"origin_group": group, "gender": "F", "true_qual": tq,
            "decision": "ESCALATE_HUMAN", "score": 0.8, "bias_risk": "high"}


def test_oracle_reduce_falsos_rechazos_de_derivados():
    escalados = [_esc("no-AR", 0.85), _esc("no-AR", 0.80), _esc("AR", 0.60)]
    dec = resolve(escalados, mode="oracle")
    assert dec == ["ADVANCE", "ADVANCE", "REJECT"]     # calificados avanzan, el otro no


def test_biased_con_bh_alto_empeora_vs_oracle():
    """El humano sesgado rechaza a calificados del grupo desfavorecido que el oracle
    aprueba — el fenómeno que B1 (censura) predice: el humano no es un árbitro gratis."""
    escalados = [_esc("no-AR", 0.85), _esc("no-AR", 0.80)]
    oracle = resolve(escalados, mode="oracle")
    biased = resolve(escalados, mode="biased", b_h=0.2)      # umbral 0.95 para no-AR
    assert oracle == ["ADVANCE", "ADVANCE"]
    assert biased == ["REJECT", "REJECT"]
    # y NO castiga al grupo de referencia
    assert resolve([_esc("AR", 0.80)], mode="biased", b_h=0.2) == ["ADVANCE"]


def test_noisy_es_determinista_con_seed():
    escalados = [_esc("no-AR", 0.85) for _ in range(20)]
    a = resolve(escalados, mode="noisy", seed=7, epsilon=0.3)
    b = resolve(escalados, mode="noisy", seed=7, epsilon=0.3)
    c = resolve(escalados, mode="noisy", seed=8, epsilon=0.3)
    assert a == b
    assert a != c                                      # otra seed, otro ruido
    assert any(d == "REJECT" for d in a)               # con ε=0.3 y n=20, hay flips


def test_modo_invalido():
    with pytest.raises(ValueError):
        resolve([], mode="jefe")
