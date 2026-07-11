"""C4 — calibración: ECE baja tras isotónica/Platt sobre scores sesgados conocidos."""
import numpy as np
import pytest

from moav_hr.core.calibration import ece, isotonic, platt


def _datos_sesgados(n=4000, seed=3):
    """Scores DISTORSIONADOS de una probabilidad verdadera: s = p_true**3 (subconfiado
    en el rango alto). Las etiquetas siguen p_true — el score crudo está mal calibrado."""
    rng = np.random.default_rng(seed)
    p_true = rng.random(n)
    labels = (rng.random(n) < p_true).astype(int)
    scores = p_true ** 3
    return scores.tolist(), labels.tolist()


def test_ece_detecta_la_descalibracion():
    scores, labels = _datos_sesgados()
    assert ece(scores, labels) > 0.15


def test_isotonic_baja_el_ece():
    scores, labels = _datos_sesgados()
    antes = ece(scores, labels)
    cal = isotonic(scores, labels)
    despues = ece(cal(scores).tolist(), labels)
    assert despues < antes / 3            # mejora sustancial, no marginal


def test_platt_baja_el_ece():
    scores, labels = _datos_sesgados()
    antes = ece(scores, labels)
    cal = platt(scores, labels)
    despues = ece(cal(scores).tolist(), labels)
    assert despues < antes


def test_ece_perfectamente_calibrado_cerca_de_cero():
    rng = np.random.default_rng(9)
    p = rng.random(20000)
    labels = (rng.random(20000) < p).astype(int)
    assert ece(p.tolist(), labels.tolist()) < 0.02


def test_ece_valida_entradas():
    with pytest.raises(ValueError):
        ece([], [])
