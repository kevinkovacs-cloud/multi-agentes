"""
Compartición de teorías en el modo LLC — bloque E · E3 (punto 2a del pedido).

Fuente: Ierache (2010), §4.3.1 (pp. 69–70, axiomas de compartición) y §4.4.8 (Alg. 4.9,
cooperación, p. 109; Alg. 4.10, colaboración, p. 116). Las reglas de fusión son las de
`core/sharing.py` (fieles a los algoritmos); con la semántica LLC (k_own = P) conservan
ΣP = K.

Gobierno de Ω (pre-registro v2, cambio 4): se rechaza al donante si hay evidencia de sesgo
en sus decisiones (LCB_δ(|Δ_DP|) > τ_b sobre TODAS sus decisiones, una evaluación por
operación) o si no tiene historia mínima (`can_donate`, A9). La reputación r se informa.
Los axiomas se verifican con los métodos existentes (`transfer_to`, `cooperate_with`): si
se violan, la operación se rechaza con el mensaje del código. Genérico: no importa
`instances/`.
"""
from __future__ import annotations
from typing import Callable, Optional

from moav_hr.core.theory import TheoryBase, theory_key, violaciones_invariante_llc

AXIOMA_COOPERACION = ("§4.3.1 [a] (p. 70): la cooperación se realiza solo entre SARs que se "
                      "encuentran con el mismo estado de evolución")
AXIOMA_COLABORACION = ("§4.3.1 [b] (p. 70): la colaboración se presenta entre un SAR en un "
                       "estado de evolución superior y un SAR receptor en un estado inferior")


def _pk(base: TheoryBase, t) -> Optional[dict]:
    e = base.find_equal(t)
    return None if e is None else {"p": e.p, "k": e.k, "u": round(e.u, 4)}


def clasificar(donante_base: TheoryBase, receptor_base: TheoryBase) -> dict:
    """Para cada teoría del donante: igual / similar / nueva respecto del receptor (antes)."""
    out = {}
    for t in donante_base.theories:
        if receptor_base.find_equal(t) is not None:
            cat = "igual"
        elif receptor_base.find_similar(t) is not None:
            cat = "similar"
        else:
            cat = "nueva"
        out[theory_key(t, donante_base.q)] = cat
    return out


def compartir(op: str, donante, receptor, monitor, decisiones: dict, m0: int,
              delta: float, es_acierto: Optional[Callable] = None) -> dict:
    """
    op = "colaboracion": `donante` (colaborador) → `receptor`; la base queda en el receptor.
    op = "cooperacion": `donante` y `receptor` son pares; los dos aportan y la base común
    queda en ambos (los dos son donantes: Ω evalúa a ambos).
    `decisiones[nombre]` = lista de {atributo, "decision"} de cada agente (plano de auditoría).
    """
    if op not in ("colaboracion", "cooperacion"):
        raise ValueError("op debe ser 'colaboracion' o 'cooperacion'")
    aportantes = [donante] if op == "colaboracion" else [donante, receptor]
    omega = {}
    for ag in aportantes:
        ev = monitor.gate_evidencia_sesgo(decisiones.get(ag.name, []), 1, delta)
        omega[ag.name] = {"can_donate": ag.can_donate(m0), "ventanas": ag.windows_observed,
                          "reputacion_informada": ag.reputation(), "evidencia_sesgo": ev}
    estados = {"donante": donante.maturity.label, "receptor": receptor.maturity.label}
    antes_r = {theory_key(t, receptor.theories.q): (t.p, t.k) for t in receptor.theories.theories}
    clasif = clasificar(donante.theories, receptor.theories)
    pk_antes = {theory_key(t, donante.theories.q): {"en_donante": {"p": t.p, "k": t.k,
                                                                    "u": round(t.u, 4)},
                                                     "en_receptor_antes": _pk(receptor.theories, t)}
                for t in donante.theories.theories}
    res = {"op": op, "donante": donante.name, "receptor": receptor.name, "estados": estados,
           "omega": omega, "base_receptor_antes": len(receptor.theories),
           "base_donante": len(donante.theories)}
    gate_ok = all(o["evidencia_sesgo"]["aprueba"] for o in omega.values())
    if not gate_ok:
        res.update(aceptada=False, motivo="Ω: evidencia de sesgo en las decisiones del donante")
        return res
    try:
        if op == "colaboracion":
            rep = donante.transfer_to(receptor, tau=0.0, m0=m0)      # axioma [b] + A9
        else:                                          # axioma [a] y A9 de los DOS pares,
            if donante.role != receptor.role:            # antes de fusionar
                raise ValueError("cooperación inválida: roles distintos")
            if donante.maturity != receptor.maturity:
                raise ValueError("la cooperación requiere mismo estado de evolución (Def. 7)")
            for ag in (donante, receptor):
                if not ag.can_donate(m0):
                    raise ValueError(f"el par {ag.name} no puede aportar sin historia de "
                                     f"equidad (A9: requiere ≥{m0} ventanas, tiene "
                                     f"{ag.windows_observed})")
            rep = donante.cooperate_with(receptor, tau=0.0, m0=m0)
    except ValueError as exc:
        axioma = AXIOMA_COLABORACION if op == "colaboracion" else AXIOMA_COOPERACION
        msg = str(exc)
        res.update(aceptada=False, motivo=f"rechazada por el código: {msg}",
                   axioma=axioma if "estado" in msg or "nivel" in msg else None)
        return res
    if es_acierto is not None:                         # U(Si, A) con las cuentas fusionadas
        receptor.theories.recalcular_u_accion_todas(es_acierto)
        if op == "cooperacion":
            donante.theories.recalcular_u_accion_todas(es_acierto)
    filas = []
    for clave, cat in clasif.items():
        filas.append({"clave": list(clave), "categoria": cat, **pk_antes[clave],
                      "en_receptor_despues": next(({"p": x.p, "k": x.k, "u": round(x.u, 4)}
                                                   for x in receptor.theories.theories
                                                   if theory_key(x, receptor.theories.q) == clave),
                                                  None)})
    conteo = {c: sum(1 for f in filas if f["categoria"] == c) for c in ("igual", "similar", "nueva")}
    res.update(aceptada=True, motivo="axiomas, can_donate y Ω sin evidencia de sesgo",
               reporte={"reforzadas": rep.reinforced, "debilitadas": rep.weakened,
                        "transferidas": rep.transferred},
               conteo=conteo, teorias=filas, base_receptor_despues=len(receptor.theories),
               invariante_receptor=violaciones_invariante_llc(receptor.theories) == [],
               invariante_donante=violaciones_invariante_llc(donante.theories) == [],
               claves_receptor_antes=len(antes_r))
    return res
