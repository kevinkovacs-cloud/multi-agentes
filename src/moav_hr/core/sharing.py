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
    return Theory(si=t.si, a=t.a, sf=t.sf, p=t.p, k=t.k, u=t.u, k_own=t.k_own)


def _merge(base_a: TheoryBase, base_b: TheoryBase, rep: ShareReport) -> list[Theory]:
    """
    Fusión por CELDAS (A1) — generaliza los Alg. 4.9/4.10 de la fuente (que tratan
    pares) al caso n>2 variantes, como extensión declarada (SOLUCIONES_AUDITORIA §A1):

      · celda = (Q(Si), A); variante = Q(Sf) dentro de la celda;
      · teorías IGUALES (misma celda y variante) suman P y K propio;
      · dentro de una celda, cada variante conserva SU P ("P del aportante") y el K
        expuesto de todas es la SUMA de los K propios de todo el grupo;
      · variantes sin correspondencia se copian tal cual.

    El K PROPIO (k_own) es el contador aditivo que se conserva entre fusiones; el K
    expuesto (k) se deriva por celda en cada fusión. Con eso la fusión es asociativa
    y conmutativa a nivel de contadores (multiconjunto de (celda, variante, P, K_propio))
    y deja de depender del orden de comparación ("primera hallada" del esquema viejo).
    """
    if base_a.q is not base_b.q:
        raise ValueError("las bases deben compartir la función de cuantización Q")
    q = base_a.q
    cells: "dict[tuple, dict]" = {}
    for source, base in (("a", base_a), ("b", base_b)):
        for t in base.theories:
            cell = (q(t.si), t.a)
            var = q(t.sf)
            slot = cells.setdefault(cell, {}).setdefault(var, {
                "si": t.si, "a": t.a, "sf": t.sf, "p": 0, "k_own": 0,
                "u": t.u, "sources": set()})
            slot["p"] += t.p
            slot["k_own"] += t.k_own
            slot["sources"].add(source)

    merged: list[Theory] = []
    for variants in cells.values():
        k_total = sum(v["k_own"] for v in variants.values())
        for v in variants.values():
            if v["sources"] == {"a", "b"}:
                rep.reinforced += 1
            merged.append(Theory(si=v["si"], a=v["a"], sf=v["sf"], p=v["p"],
                                 k=k_total, u=v["u"], k_own=v["k_own"]))
        if len(variants) > 1:
            rep.weakened += len(variants) - 1
        if all(v["sources"] == {"b"} for v in variants.values()):
            rep.transferred += len(variants)
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
    base_i.replace_all([_copy(t) for t in merged])   # contenido común, copias por agente;
    base_j.replace_all([_copy(t) for t in merged])   # replace_all re-indexa y re-estampa
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
    receptor.replace_all(merged)                     # solo el receptor (Alg. 4.10)
    return rep
