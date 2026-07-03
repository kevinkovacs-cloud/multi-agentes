"""
Operadores de compartición de teorías entre agentes — fieles a la fuente del LLC.

FUENTE VERIFICADA (03/07/2026): Ierache (2010), tesis doctoral, SEDICI-UNLP
(http://sedici.unlp.edu.ar/handle/10915/18378), Algoritmo 4.9 (cooperación, pág. 108)
y Algoritmo 4.10 (colaboración, pág. 115), que implementan el método de intercambio de
Maceri & García-Martínez (2001; García-Martínez et al. 2006, LNAI 4140).

Reglas de la fuente (idénticas en ambos operadores; cambia quién recibe el resultado):
se construye una base NUEVA con dos pasadas —una por cada base de origen—:
  · teoría IGUAL en la otra base   → entra una sola vez con P y K sumados;
  · teoría SIMILAR en la otra base → entra CADA variante conservando SU propia P
    ("la P del aportante") y con K = suma de los K del par similar;
  · sin correspondencia            → entra copiada tal cual.
En cooperación (Def. 7) la base resultante es COMÚN: "se asigna la BCCRAB para ser
aplicada por RA y RB" — acá se materializa como contenido idéntico replicado en cada
agente (copias por agente, para no acoplar mutaciones posteriores entre bases).
En colaboración (Def. 8) la base resultante (BCCRR) se asigna SOLO al receptor.
La U no participa del intercambio en la fuente (se recalcula en la región 4); se
conserva la U propia de cada teoría que entra.

Def. 9: toda compartición se condiciona a la reputación del donante (rⱼ ≥ τ).
"""
from __future__ import annotations
from dataclasses import dataclass

from moav_hr.core.theory import Theory, TheoryBase


@dataclass
class ShareReport:
    op: str                       # "cooperation" | "collaboration"
    accepted: bool                # rⱼ ≥ τ (Def. 9)
    reinforced: int = 0           # pares IGUALES fusionados (P y K sumados)
    weakened: int = 0             # pares SIMILARES (ambas variantes entran, K sumado)
    transferred: int = 0          # teorías sin correspondencia copiadas desde el donante
    reason: str = ""


def _copy(t: Theory) -> Theory:
    return Theory(si=t.si, a=t.a, sf=t.sf, p=t.p, k=t.k, u=t.u)


def _merge(base_a: TheoryBase, base_b: TheoryBase, rep: ShareReport) -> list[Theory]:
    """
    Dos pasadas del Alg. 4.9/4.10: recorre A contra B y luego B contra A.
    Si hay varias similares, se usa la primera hallada (la fuente no desambigua).
    """
    merged: list[Theory] = []
    # pasada 1 — teorías de A contra B
    for ta in base_a.theories:
        tb = base_b.find_equal(ta)
        if tb is not None:
            merged.append(Theory(si=ta.si, a=ta.a, sf=ta.sf,
                                 p=ta.p + tb.p, k=ta.k + tb.k, u=ta.u))
            rep.reinforced += 1
            continue
        tb = base_b.find_similar(ta)
        if tb is not None:
            merged.append(Theory(si=ta.si, a=ta.a, sf=ta.sf,
                                 p=ta.p, k=ta.k + tb.k, u=ta.u))   # P del aportante (A)
            rep.weakened += 1
            continue
        merged.append(_copy(ta))
    # pasada 2 — teorías de B contra A (las iguales ya entraron en la pasada 1)
    for tb in base_b.theories:
        if base_a.find_equal(tb) is not None:
            continue
        ta = base_a.find_similar(tb)
        if ta is not None:
            merged.append(Theory(si=tb.si, a=tb.a, sf=tb.sf,
                                 p=tb.p, k=ta.k + tb.k, u=tb.u))   # P del aportante (B)
            continue
        merged.append(_copy(tb))
        rep.transferred += 1
    return merged


def cooperate(base_i: TheoryBase, base_j: TheoryBase,
              donor_reputation: float = 1.0, tau: float = 0.0) -> ShareReport:
    """
    Def. 7 — cooperación entre pares (mismo estado y capa). Alg. 4.9 (Ierache 2010).
    Genera la base COMÚN y la asigna a AMBOS agentes (contenido idéntico, copias por
    agente). Condicionada por Def. 9: solo si donor_reputation ≥ tau.
    """
    rep = ShareReport("cooperation", accepted=donor_reputation >= tau)
    if not rep.accepted:
        rep.reason = f"reputación {donor_reputation:.3f} < τ {tau:.3f}"
        return rep
    merged = _merge(base_i, base_j, rep)
    base_i.theories[:] = [_copy(t) for t in merged]   # in-place: preserva el binding
    base_j.theories[:] = [_copy(t) for t in merged]   # del retriever de cada agente
    return rep


def collaborate(receptor: TheoryBase, colaborador: TheoryBase,
                donor_reputation: float = 1.0, tau: float = 0.0) -> ShareReport:
    """
    Def. 8 — colaboración maestro→aprendiz (nivel(colaborador) ≻ nivel(receptor)).
    Alg. 4.10 (Ierache 2010): mismas reglas de fusión; la base resultante (BCCRR) se
    asigna SOLO al receptor. La condición de niveles se valida en transfer_to.
    Condicionada por Def. 9: solo si donor_reputation ≥ tau.
    """
    rep = ShareReport("collaboration", accepted=donor_reputation >= tau)
    if not rep.accepted:
        rep.reason = f"reputación {donor_reputation:.3f} < τ {tau:.3f}"
        return rep
    merged = _merge(receptor, colaborador, rep)
    receptor.theories[:] = merged
    return rep
