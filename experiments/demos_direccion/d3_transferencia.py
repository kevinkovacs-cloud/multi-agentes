#!/usr/bin/env python
"""
D3 — Transferencia entre dos agentes del mismo rol, con gating por reputación (pedido P2).

Funciones existentes: MOACVAgent.transfer_to (colaboración, Def. 8 / Alg. 4.10),
core.sharing.collaborate, Monitor.approve_sharing (Def. 9) y MOACVAgent.can_donate (A9).

  · Donante A: el Matcher de la PoC (Trained), con la base del warmup y la historia de
    fair(W) de las ventanas de la PoC, calculada como en run_poc.py (3 ventanas).
  · Receptor B: un Matcher en Born que atendió la tarea 2 (tarea2.py) aprendiendo en
    línea desde una base vacía: llega a la transferencia con base propia.
  · Contraejemplo 1: donante C, Trained, con historia de fair(W) baja: es el Matcher que
    recorrió las tareas 1 y 2 en línea (D2); su reputación sale de esas 6 ventanas.
  · Contraejemplo 2: donante A∅, igual a A pero sin ventanas observadas (can_donate False).

Para cada teoría de A se informa si entra en B como IGUAL, SIMILAR o NUEVA (reglas de los
Alg. 4.9/4.10 que implementa sharing._merge) y con qué P y K queda.

Uso:  python experiments/demos_direccion/d3_transferencia.py [--out DIR]
"""
from __future__ import annotations
import argparse
import inspect

from comun import (ATTR, C_AZUL, C_ROJO, C_TEXTO, C_VERDE, CRITERIO, ejecutar_tarea,
                   estilo_figuras, guardar_figura, guardar_json, num, out_dir,
                   pie_rotulos, pipeline_vacio, plt, si_corta, teoria_dict)
from tarea2 import generar_tarea2
from moav_hr.core import fairness
from moav_hr.core.agent import MOACVAgent
from moav_hr.core.theory import q_canonical
from moav_hr.instances.hr.pipeline import HRPipeline, matcher_view, record_of
from moav_hr.instances.hr.synthetic import CANDIDATES


def donante_poc(con_historia: bool = True):
    """El Matcher de la PoC: warmup + (opcional) fair(W) de sus ventanas, como run_poc."""
    pipe = HRPipeline(mode="sim")
    pipe.warmup(CANDIDATES)
    recs = [record_of(pipe.process(c)) for c in CANDIDATES]
    if con_historia:
        w = max(1, len(recs) // 3)                     # W_SUB de run_poc
        for i in range(0, len(recs), w):
            pipe.matcher.record_window_fairness(
                fairness.fair_window(matcher_view(recs[i:i + w]), ATTR, CRITERIO))
    return pipe


def receptor_born():
    """Matcher en Born que aprendió en línea sobre la tarea 2 (base propia)."""
    pipe = pipeline_vacio(nacido=True)
    ejecutar_tarea(pipe, generar_tarea2(), 2)
    return pipe.matcher


def donante_historia_baja():
    """Matcher Trained que recorrió las tareas 1 y 2 en línea (D2): 6 ventanas."""
    pipe = pipeline_vacio()
    ejecutar_tarea(pipe, CANDIDATES, 1)
    ejecutar_tarea(pipe, generar_tarea2(), 2)
    return pipe.matcher


def _pk(base, t):
    """(P, K) de la variante de t en `base` (misma celda y Sf), o None si no está."""
    e = base.find_equal(t)
    return None if e is None else {"p": e.p, "k": e.k}


def _intento(donante, receptor, tau, etiqueta):
    """Intenta la colaboración donante→receptor; nunca deja escapar la excepción."""
    antes = len(receptor.theories)
    estado_antes = receptor.maturity.label
    res = {"donante": etiqueta, "estado_donante": donante.maturity.label,
           "ventanas_donante": donante.windows_observed,
           "fair_w_donante": list(donante._fair_history),
           "reputacion_donante": donante.reputation(), "tau": tau,
           "can_donate": donante.can_donate()}
    try:
        rep = donante.transfer_to(receptor, tau=tau)
        res.update({"aceptada": rep.accepted, "motivo": rep.reason or "r ≥ τ",
                    "iguales_reforzadas": rep.reinforced, "similares": rep.weakened,
                    "nuevas": rep.transferred})
    except ValueError as exc:
        res.update({"aceptada": False, "motivo": f"transfer_to lanza ValueError: {exc}"})
    res.update({"base_receptor_antes": antes, "base_receptor_despues": len(receptor.theories),
                "estado_receptor_antes": estado_antes,
                "estado_receptor_despues": receptor.maturity.label})
    return res


def _figura(escenarios, filas, tau, destino):
    fig = plt.figure(figsize=(9, 8.2))
    ar = fig.add_axes([0.08, 0.64, 0.4, 0.21])
    at = fig.add_axes([0.53, 0.6, 0.46, 0.27]); at.axis("off")
    ab = fig.add_axes([0.012, 0.22, 0.976, 0.33]); ab.axis("off")
    nombres = [e["donante_corto"] for e in escenarios]
    reps = [e["reputacion_donante"] for e in escenarios]
    colores = [C_VERDE if e["aceptada"] else C_ROJO for e in escenarios]
    barras = ar.barh(nombres, reps, color=colores, height=0.6)
    for b, e in zip(barras, escenarios):
        if e["ventanas_donante"] == 0:
            b.set_hatch("//"); b.set_edgecolor("white")
    ar.axvline(tau, color=C_TEXTO, lw=2, ls="--")
    ar.set_title(f"reputación r del donante frente a τ = {num(tau, 1)} (línea)", fontsize=12)
    for i, r in enumerate(reps):
        ar.annotate(num(r, 3), (0.02, i), va="center", ha="left", fontsize=12,
                    color="white", fontweight="bold",
                    bbox=dict(boxstyle="square,pad=0.15", fc=colores[i], ec="none"))
    ar.set_xlim(0, 1.18)
    ar.invert_yaxis()
    ar.set_xticks([0, 0.5, 1.0], ["0", "0,5", "1"])
    lineas = []
    for e in escenarios:
        marca = "✓ aceptada" if e["aceptada"] else "✗ rechazada"
        lineas.append(f"{e['donante_corto']}: {marca}")
        if e["aceptada"]:
            lineas.append(f"   igual {e['iguales_reforzadas']} · similar {e['similares']} · "
                          f"nueva {e['nuevas']}")
        else:
            lineas.append("   " + e["motivo_corto"])
        lineas.append(f"   base de B: {e['base_receptor_antes']} → {e['base_receptor_despues']}"
                      f" · B: {e['estado_receptor_antes']} → {e['estado_receptor_despues']}")
    at.text(0, 1, "\n".join(lineas), va="top", ha="left", fontsize=12, color=C_TEXTO,
            linespacing=1.4)
    cab = (f"{'T':<4}{'Si de la teoría de A':<34}{'acc':<5}{'entra como':<11}"
           f"{'en A':>6}{'B antes':>9}{'B después':>11}")
    tabla = [cab, "─" * len(cab)]
    for f in filas:
        pk = lambda d: "—" if d is None else f"{d['p']}/{d['k']}"  # noqa: E731
        tabla.append(f"T{f['id']:<3}{si_corta(f['si']):<34}{f['a'][:3]:<5}{f['categoria']:<11}"
                     f"{pk(f['en_A']):>6}{pk(f['en_B_antes']):>9}{pk(f['en_B_despues']):>11}")
    ab.text(0, 1, "\n".join(tabla), va="top", ha="left", family="DejaVu Sans Mono",
            fontsize=12, color=C_TEXTO, linespacing=1.35)
    fig.suptitle("D3 · Transferencia maestro → aprendiz del mismo rol (Def. 8, gating Def. 9)",
                 x=0.012, ha="left", y=0.975, fontsize=14)
    fig.text(0.012, 0.93, "Donantes: A = Matcher de la PoC · C = Matcher con fair(W) baja · "
             "A∅ = A sin ventanas.\nReceptor B = Matcher en Born con base propia (tarea 2).",
             fontsize=12, color=C_TEXTO, va="top")
    pie_rotulos(fig, [
        "Tabla: cada teoría del donante A y cómo entra en B (P/K; acc = acción). "
        "Igual = misma Si, A y Sf "
        "(suma P y K) · similar = misma Si y A, otro Sf · nueva = se copia. Barra rayada: "
        "sin historia, r es el prior r0 (no evidencia)."], ancho=98)
    return guardar_figura(fig, "d3_transferencia.png", destino)


def correr(out=None) -> dict:
    destino = out_dir(out)
    estilo_figuras()
    pipe_a = donante_poc()
    A, monitor = pipe_a.matcher, pipe_a.monitor
    tau = monitor.tau

    # escenario principal: A → B
    B = receptor_born()
    base_b_antes = [teoria_dict(t) for t in B.theories.theories]
    cat = {}
    for t in A.theories.theories:
        if B.theories.find_equal(t) is not None:
            cat[t.id] = "igual"
        elif B.theories.find_similar(t) is not None:
            cat[t.id] = "similar"
        else:
            cat[t.id] = "nueva"
    antes = {t.id: _pk(B.theories, t) for t in A.theories.theories}
    aprobacion_omega = monitor.approve_sharing(A)
    principal = _intento(A, B, tau, "A: Matcher de la PoC")
    filas = [{"id": t.id, "si": t.si, "a": t.a, "sf": t.sf, "categoria": cat[t.id],
              "en_A": {"p": t.p, "k": t.k}, "en_B_antes": antes[t.id],
              "en_B_despues": _pk(B.theories, t)} for t in A.theories.theories]

    # contraejemplo 1: donante con historia de fair(W) baja
    C = donante_historia_baja()
    B1 = receptor_born()
    contra1 = _intento(C, B1, tau, "C: Matcher con historia de fair(W) baja")
    contra1["aprobacion_omega"] = monitor.approve_sharing(C)

    # contraejemplo 2: donante sin historia (A9)
    A0 = donante_poc(con_historia=False).matcher
    B2 = receptor_born()
    contra2 = _intento(A0, B2, tau, "A∅: Matcher de la PoC sin ventanas observadas")
    contra2["aprobacion_omega"] = monitor.approve_sharing(A0)
    contra2["nota"] = ("approve_sharing solo mira r ≥ τ y, sin historia, r es el prior r0; "
                       "can_donate (A9) es el que frena al donante sin historia")

    m0 = inspect.signature(MOACVAgent.can_donate).parameters["m0"].default
    contra2["ventanas_minimas_para_donar"] = m0
    for e, corto, motivo in (
            (principal, "A", ""),
            (contra1, "C", f"r = {num(contra1['reputacion_donante'], 3)} < τ = {num(tau, 1)}"),
            (contra2, "A∅", f"can_donate = {contra2['can_donate']} "
                            f"({contra2['ventanas_donante']} ventanas; hacen falta {m0})")):
        e["donante_corto"] = corto
        e["motivo_corto"] = motivo
    figura = _figura([principal, contra1, contra2], filas, tau, destino)
    conteo = {c: sum(1 for f in filas if f["categoria"] == c) for c in ("igual", "similar", "nueva")}
    salida = {
        "demo": "D3 — transferencia maestro→aprendiz del mismo rol con gating por reputación (P2)",
        "operador": "MOACVAgent.transfer_to → core.sharing.collaborate (Def. 8, Alg. 4.10); "
                    "la base resultante se asigna solo al receptor",
        "tau": tau,
        "cuantizacion": "q_canonical" if A.theories.q is q_canonical else str(A.theories.q),
        "donante_A": {"estado": A.maturity.label, "fair_w": list(A._fair_history),
                      "reputacion": A.reputation(), "can_donate": A.can_donate(),
                      "aprobacion_omega": aprobacion_omega,
                      "base": [teoria_dict(t) for t in A.theories.theories]},
        "receptor_B": {"estado_antes": principal["estado_receptor_antes"],
                       "estado_despues": principal["estado_receptor_despues"],
                       "base_antes": base_b_antes,
                       "base_despues": [teoria_dict(t) for t in B.theories.theories]},
        "principal": principal,
        "teorias_de_A_en_B": filas,
        "conteo_por_categoria": conteo,
        "nota_similares": (None if conteo["similar"] else
                           "ninguna teoría de A comparte celda (Si, A) con una teoría de B "
                           "que tenga otro Sf: en estos lotes, la misma Si con la misma "
                           "acción tuvo siempre el mismo resultado"),
        "contraejemplo_r_bajo": contra1,
        "contraejemplo_sin_historia": contra2,
        "cambia_el_estado_de_B": principal["estado_receptor_antes"] != principal["estado_receptor_despues"],
        "figuras": [figura.name],
    }
    guardar_json(salida, "d3_transferencia.json", destino)
    return salida


def main() -> None:
    ap = argparse.ArgumentParser(description="D3 — transferencia entre agentes del mismo rol")
    ap.add_argument("--out", default=None, help="carpeta de salida (default docs/demos_direccion)")
    s = correr(ap.parse_args().out)
    p = s["principal"]
    print(f"D3 · A→B aceptada={p['aceptada']} (r={s['donante_A']['reputacion']}, τ={s['tau']}) · "
          f"categorías {s['conteo_por_categoria']} · base B {p['base_receptor_antes']}→"
          f"{p['base_receptor_despues']} · C aceptada={s['contraejemplo_r_bajo']['aceptada']} · "
          f"A∅ aceptada={s['contraejemplo_sin_historia']['aceptada']}")


if __name__ == "__main__":
    main()
