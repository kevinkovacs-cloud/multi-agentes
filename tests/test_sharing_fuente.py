"""
Def. 7/8 fieles a la FUENTE — Ierache (2010), Alg. 4.9 y 4.10 (SEDICI, págs. 108/115).

Verifica lo que el código anterior divergía del original:
  (a) la cooperación genera una base COMÚN aplicada por ambos agentes;
  (b) en teorías SIMILARES entra CADA variante conservando SU propia P
      ("la P del aportante") con K = suma del par;
  (c) en la colaboración, la base resultante se asigna SOLO al receptor.
"""
from moav_hr.core.theory import Theory, TheoryBase
from moav_hr.core.sharing import cooperate, collaborate


def _t(sf_val: int, p: int, k: int) -> Theory:
    # misma Si y A → "similar" cuando difiere la Sf (equivalencia exacta por default)
    return Theory(si={"x": 1}, a="A", sf={"r": sf_val}, p=p, k=k)


def test_cooperacion_genera_base_comun_en_ambos():
    """Alg. 4.9: 'se asigna la BCCRAB para ser aplicada por RA y RB'."""
    bi, bj = TheoryBase(), TheoryBase()
    bi.add(_t(sf_val=1, p=2, k=3))
    bj.add(_t(sf_val=1, p=4, k=5))          # igual (Si, A, Sf)
    rep = cooperate(bi, bj)
    assert rep.reinforced == 1
    # la fusión (P y K sumados) queda en AMBAS bases, no solo en la del receptor
    for base in (bi, bj):
        assert len(base) == 1
        assert (base.theories[0].p, base.theories[0].k) == (6, 8)


def test_cooperacion_similar_conserva_P_del_aportante():
    """Alg. 4.9, caso similar: ambas variantes entran, cada una con SU P y K sumado."""
    bi, bj = TheoryBase(), TheoryBase()
    bi.add(_t(sf_val=1, p=2, k=3))          # variante de A
    bj.add(_t(sf_val=2, p=4, k=5))          # similar (misma Si y A, otra Sf)
    rep = cooperate(bi, bj)
    assert rep.weakened == 1
    for base in (bi, bj):
        assert len(base) == 2               # las DOS variantes están
        por_sf = {t.sf["r"]: t for t in base.theories}
        assert (por_sf[1].p, por_sf[1].k) == (2, 8)   # P del aportante A · K sumado
        assert (por_sf[2].p, por_sf[2].k) == (4, 8)   # P del aportante B · K sumado


def test_colaboracion_similar_agrega_variante_del_colaborador():
    """Alg. 4.10: la variante del colaborador también entra (con su P, K sumado)."""
    recep, colab = TheoryBase(), TheoryBase()
    recep.add(_t(sf_val=1, p=1, k=2))
    colab.add(_t(sf_val=2, p=7, k=9))       # similar a la del receptor
    rep = collaborate(recep, colab, donor_reputation=1.0, tau=0.0)
    assert rep.accepted
    assert len(recep) == 2                   # receptor termina con ambas variantes
    por_sf = {t.sf["r"]: t for t in recep.theories}
    assert (por_sf[1].p, por_sf[1].k) == (1, 11)      # su variante: propia P, K sumado
    assert (por_sf[2].p, por_sf[2].k) == (7, 11)      # variante del colaborador: P propia
    assert len(colab) == 1                   # la base del colaborador NO se toca
