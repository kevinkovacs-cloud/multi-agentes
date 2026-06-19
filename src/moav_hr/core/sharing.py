"""
Operadores de compartición de teorías entre agentes.

v13 §2.3 / Def. 7 (cooperación, pares simétrica), Def. 8 (colaboración maestro→aprendiz,
asimétrica), Def. 9 (reputación de equidad y ponderación: toda transferencia exige rⱼ ≥ τ).
"""
from __future__ import annotations
from dataclasses import dataclass

from moav_hr.core.theory import Theory, TheoryBase


@dataclass
class ShareReport:
    op: str                       # "cooperation" | "collaboration"
    accepted: bool                # rⱼ ≥ τ (Def. 9)
    reinforced: int = 0
    weakened: int = 0
    transferred: int = 0
    reason: str = ""


def cooperate(base_i: TheoryBase, base_j: TheoryBase,
              donor_reputation: float = 1.0, tau: float = 0.0) -> ShareReport:
    """
    Def. 7 — cooperación entre pares (mismo estado y capa). Simétrica.
    Igual → P_c=P_i+P_j, K_c=K_i+K_j. Similar → K_c=K_i+K_j, P del aportante.
    Sin correspondencia → se copia (P,K) sin cambios.
    Condicionada por Def. 9: solo si donor_reputation ≥ tau.
    """
    rep = ShareReport("cooperation", accepted=donor_reputation >= tau)
    if not rep.accepted:
        rep.reason = f"reputación {donor_reputation:.3f} < τ {tau:.3f}"
        return rep
    for tj in base_j.theories:
        eq = base_i.find_equal(tj)
        if eq is not None:
            eq.p += tj.p
            eq.k += tj.k
            rep.reinforced += 1
            continue
        sim = base_i.find_similar(tj)
        if sim is not None:
            sim.k += tj.k  # suma K; conserva P del aportante (no se baja P de sim)
            rep.weakened += 1
            continue
        base_i.add(Theory(si=tj.si, a=tj.a, sf=tj.sf, p=tj.p, k=tj.k, u=tj.u))
        rep.transferred += 1
    return rep


def collaborate(receptor: TheoryBase, colaborador: TheoryBase,
                donor_reputation: float = 1.0, tau: float = 0.0) -> ShareReport:
    """
    Def. 8 — colaboración maestro→aprendiz (nivel(colaborador) ≻ nivel(receptor)).
    Igual → refuerza (P+=, K+=). Similar → debilita (solo K+=). Inexistente → transfiere.
    Condicionada por Def. 9: solo si donor_reputation ≥ tau.
    La condición de niveles se valida en MOACVAgent.transfer_to (usa el orden total).
    """
    rep = ShareReport("collaboration", accepted=donor_reputation >= tau)
    if not rep.accepted:
        rep.reason = f"reputación {donor_reputation:.3f} < τ {tau:.3f}"
        return rep
    for tj in colaborador.theories:
        eq = receptor.find_equal(tj)
        if eq is not None:
            eq.p += tj.p
            eq.k += tj.k
            rep.reinforced += 1
            continue
        sim = receptor.find_similar(tj)
        if sim is not None:
            sim.k += tj.k  # debilita: suma K sin sumar P
            rep.weakened += 1
            continue
        receptor.add(Theory(si=tj.si, a=tj.a, sf=tj.sf, p=tj.p, k=tj.k, u=tj.u))
        rep.transferred += 1
    return rep
