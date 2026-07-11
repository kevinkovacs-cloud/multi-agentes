"""A3+N2 — D = (1−ρ̄)/2 sin clamp, precondiciones y cota de alcanzabilidad d_max."""
import pytest

from moav_hr.core import fairness


def test_anticorrelados_dan_D_igual_1_sin_saturar():
    series = {"a": [1.0, -1.0, 1.0, -1.0], "b": [-1.0, 1.0, -1.0, 1.0]}   # ρ = −1
    assert fairness.diversity(series) == 1.0


def test_clones_dan_D_cero():
    series = {"a": [0.1, 0.2, 0.3, 0.4], "b": [0.1, 0.2, 0.3, 0.4]}       # ρ = 1
    assert fairness.diversity(series) == 0.0


def test_independientes_rondan_un_medio():
    series = {"a": [1.0, -1.0, 1.0, -1.0], "b": [1.0, 1.0, -1.0, -1.0]}   # ρ = 0
    assert fairness.diversity(series) == pytest.approx(0.5)


def test_menos_de_dos_series_es_error():
    with pytest.raises(ValueError):
        fairness.diversity({"solo": [0.1, 0.2]})


def test_no_comparables_es_error():
    with pytest.raises(ValueError):
        fairness.diversity({"a": [1, 2], "b": [1, 2]}, comparable=False)


def test_d_max():
    assert fairness.d_max(2) == 1.0
    assert fairness.d_max(3) == 0.75
    assert fairness.d_max(5) == pytest.approx(0.625)
    with pytest.raises(ValueError):
        fairness.d_max(1)
