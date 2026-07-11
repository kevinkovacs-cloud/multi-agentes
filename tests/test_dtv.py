"""B3 — cota inferior de d_TV del canal proxy vía clasificador A-vs-A′ en held-out."""
import numpy as np

from moav_hr.core.fairness import dtv_lower_bound


def _si_sin_senal(rng, n):
    si, g = [], []
    for _ in range(n):
        si.append({"skills_match": int(rng.integers(0, 4)),
                   "exp_band": str(rng.choice(["jr", "mid", "sr"])),
                   "seniority_ok": bool(rng.integers(0, 2))})
        g.append(str(rng.choice(["AR", "no-AR"])))
    return si, g


def _si_con_proxy(rng, n, fuerza: float):
    """El campo 'registro' copia el grupo con prob. (1+fuerza)/2 — proxy graduable."""
    si, g = [], []
    for _ in range(n):
        grupo = str(rng.choice(["AR", "no-AR"]))
        copia = rng.random() < (1 + fuerza) / 2
        si.append({"skills_match": int(rng.integers(0, 4)),
                   "registro": grupo if copia else ("AR" if grupo == "no-AR" else "no-AR")})
        g.append(grupo)
    return si, g


def test_sin_senal_de_grupo_dtv_cerca_de_cero():
    rng = np.random.default_rng(42)
    si, g = _si_sin_senal(rng, 2000)
    assert dtv_lower_bound(si, g, seed=0) < 0.1


def test_proxy_fuerte_dtv_alto():
    rng = np.random.default_rng(42)
    si, g = _si_con_proxy(rng, 2000, fuerza=0.9)
    assert dtv_lower_bound(si, g, seed=0) > 0.5


def test_monotonia_aproximada_en_la_fuerza_del_proxy():
    rng = np.random.default_rng(42)
    si_debil, g_debil = _si_con_proxy(rng, 2000, fuerza=0.2)
    si_fuerte, g_fuerte = _si_con_proxy(rng, 2000, fuerza=0.8)
    assert dtv_lower_bound(si_debil, g_debil, seed=0) < dtv_lower_bound(
        si_fuerte, g_fuerte, seed=0)
