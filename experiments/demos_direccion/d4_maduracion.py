#!/usr/bin/env python
"""
D4 — Maduración sobre el caso y segunda tarea (pedido P4).

Un Matcher arranca en Born con la base vacía y recorre la tarea 1 (lote de la PoC) y la
tarea 2 (tarea2.py, la misma del D2). Cada 4 casos cierra una ventana: registra fair(W)
de las decisiones que implican sus scores e intenta avanzar con MOACVAgent.advance
(Def. 12: el paso del ciclo se ejecuta solo si Ω aprueba en gate_evolution). En la tarea
2 reutiliza las teorías aprendidas en la tarea 1.

Se corre dos veces: con el gate PUNTUAL (default: media de fair(W) de las últimas m
ventanas ≥ τ) y con el CERTIFICADO (LCB de Hoeffding de la media de todas las ventanas
≥ τ). El certificado exige historia larga: m_min(1,0) ventanas perfectas (stats.m_min_gate).
Es la propiedad del certificado, no un defecto.

Uso:  python experiments/demos_direccion/d4_maduracion.py [--out DIR]
"""
from __future__ import annotations
import argparse
import inspect
import warnings

from comun import (C_AMBAR, C_AZUL, C_ROJO, C_TEXTO, C_VERDE, C_VIOLETA, comas,
                   ejecutar_tarea, estilo_figuras, guardar_figura, guardar_json, num,
                   out_dir, pie_rotulos, pipeline_vacio, plt)
from tarea2 import generar_tarea2
from moav_hr.core import stats
from moav_hr.core.audit.trail import AuditTrail
from moav_hr.core.lifecycle import MaturityState, Region
from moav_hr.core.monitor import FairnessUtilityMonitor
from moav_hr.instances.hr.synthetic import CANDIDATES

M_TODAS = 10 ** 6            # el certificado usa TODAS las ventanas observadas
DELTA = inspect.signature(FairnessUtilityMonitor.gate_evolution).parameters["delta"].default
M_PUNTUAL = inspect.signature(FairnessUtilityMonitor.gate_evolution).parameters["m"].default


def recorrido(certificado: bool) -> dict:
    pipe = pipeline_vacio(nacido=True)
    ag, mon = pipe.matcher, pipe.monitor
    trail = AuditTrail("TRC-D4-" + ("CERT" if certificado else "PUNTUAL"))
    linea = []

    def al_cerrar(v):
        antes = ag.maturity.label
        with warnings.catch_warnings(record=True) as avisos:
            warnings.simplefilter("always")
            kw = {"m": M_TODAS, "delta": DELTA} if certificado else {}
            avanzo = ag.advance(mon, certified=certificado, trail=trail, **kw)
        hist = ag._fair_history
        media = sum(hist) / len(hist)
        linea.append({
            "ventana": len(linea) + 1, "tarea": v["tarea"], "fair_w": v["fair_w"],
            "reputacion_puntual": ag.reputation(),
            "media_todas": round(media, 4),
            "lcb_todas": round(media - stats.hoeffding_halfwidth(len(hist), DELTA), 4),
            "estado_antes": antes, "estado_despues": ag.maturity.label, "avanzo": avanzo,
            "aviso": str(avisos[0].message) if avisos else None})

    t1 = ejecutar_tarea(pipe, CANDIDATES, 1, al_cerrar_ventana=al_cerrar)
    t2 = ejecutar_tarea(pipe, generar_tarea2(), 2, al_cerrar_ventana=al_cerrar)
    llega = next((x["ventana"] for x in linea if x["estado_despues"] == "mature"), None)
    return {"linea_de_tiempo": linea, "estado_final": ag.maturity.label,
            "ventana_en_que_llega_a_mature": llega,
            "eventos_region_7": sum(1 for e in trail.events
                                    if e.region == int(Region.EVOLUTION)),
            "transiciones": [{"ventana": x["ventana"], "de": x["estado_antes"],
                              "a": x["estado_despues"]} for x in linea if x["avanzo"]],
            "tareas": (t1, t2), "tau": mon.tau}


def _reuso(t) -> dict:
    cs = t["casos"]
    con_teoria = [c for c in cs if c["seleccionada"] is not None]
    con_aciertos = [c for c in con_teoria if c["seleccionada"]["p"] >= 1]
    return {"casos": len(cs),
            "casos_con_teorias_recuperadas": len(con_teoria),
            "casos_cuya_teoria_seleccionada_tenia_aciertos": len(con_aciertos),
            "aciertos_del_matcher_en_esos_casos": sum(c["acierto"] for c in con_aciertos),
            "aciertos_del_matcher_total": sum(c["acierto"] for c in cs),
            "teorias_nuevas": t["teorias_nuevas"]}


def _figura(punt, cert, tau, m_min, destino):
    import numpy as np
    lp, lc = punt["linea_de_tiempo"], cert["linea_de_tiempo"]
    x = np.array([v["ventana"] for v in lp])
    fig = plt.figure(figsize=(9, 8.4))
    a1 = fig.add_axes([0.1, 0.55, 0.87, 0.29])
    a2 = fig.add_axes([0.1, 0.285, 0.87, 0.2], sharex=a1)
    a1.bar(x, [v["fair_w"] for v in lp], width=0.5, facecolor="none", edgecolor=C_AZUL,
           hatch="///", lw=1.8, label="fair(W) de la ventana")
    for v in lp:
        a1.annotate(num(v["fair_w"], 2), (v["ventana"], v["fair_w"]), xytext=(-18, 4),
                    textcoords="offset points", ha="right", fontsize=12, color=C_AZUL)
    a1.plot(x, [v["reputacion_puntual"] for v in lp], "-o", color=C_VERDE, lw=2.4, ms=8,
            label=f"r puntual (media de las últimas {M_PUNTUAL})")
    a1.plot(x, [v["lcb_todas"] for v in lc], "-s", color=C_VIOLETA, lw=2.4, ms=8,
            label="LCB certificada (todas las ventanas)")
    a1.axhline(tau, color=C_ROJO, lw=2, ls="--", label=f"τ = {num(tau, 1)}")
    a1.set_ylim(min(-0.45, min(v["lcb_todas"] for v in lc) - 0.1), 1.35)
    a1.set_ylabel("fair(W), r, LCB")
    a1.legend(loc="lower left", bbox_to_anchor=(0.0, 1.01), ncol=2, frameon=False,
              fontsize=12, columnspacing=1.2)
    niveles = [s.label for s in MaturityState]
    nombres = {"born": "Born", "novato": "Novice", "trained": "Trained", "mature": "Mature"}
    yp = [niveles.index(v["estado_despues"]) for v in lp]
    yc = [niveles.index(v["estado_despues"]) for v in lc]
    a2.step(np.r_[0, x], [0] + yp, where="post", color=C_VERDE, lw=3,
            label="gate puntual")
    a2.step(np.r_[0, x], [0] + yc, where="post", color=C_VIOLETA, lw=3, ls="--",
            label="gate certificado")
    a2.set_yticks(range(len(niveles)), [nombres[n] for n in niveles])
    a2.set_ylim(-0.4, len(niveles) - 0.6)
    a2.set_xlim(0.4, x[-1] + 0.6)
    a2.set_xticks(x, [f"W{v['ventana']}" for v in lp])
    a2.set_xlabel("ventana (4 casos cada una); el estado es el que queda después del gate")
    a2.legend(loc="center right", framealpha=0.95)
    corte = next((v["ventana"] for v in lp if v["tarea"] == 2), None)
    if corte is not None:
        for ax in (a1, a2):
            ax.axvline(corte - 0.5, color=C_TEXTO, lw=1.8, ls=":")
        a1.annotate("tarea 1 | tarea 2", (corte - 0.5, a1.get_ylim()[0] + 0.05),
                    ha="center", va="bottom", fontsize=12, color=C_TEXTO,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=C_TEXTO))
    comas(a1)
    plt.setp(a1.get_xticklabels(), visible=False)
    fig.suptitle("D4 · Maduración del Matcher gobernada por Ω (Def. 12) en dos tareas",
                 x=0.012, ha="left", y=0.98, fontsize=14)
    ult = lp[-1]
    caida = ""
    if ult["reputacion_puntual"] < tau and ult["estado_despues"] == "mature":
        caida = (f" En W{ult['ventana']} r puntual cae a {num(ult['reputacion_puntual'], 3)} "
                 "< τ y el estado no retrocede: advance solo avanza (ciclo monótono).")
    pie_rotulos(fig, [
        f"Puntual: llega a Mature en la ventana {punt['ventana_en_que_llega_a_mature']}.{caida} "
        f"Certificado: queda en {nombres[cert['estado_final']]} tras {len(lc)} ventanas; "
        f"aun con ventanas perfectas necesita m_min(1,0) = {m_min} (τ = {num(tau, 1)}, "
        f"δ = {num(DELTA, 2)}). Es la propiedad del certificado, no un defecto. "
        "Ventanas de 4 casos: fair(W) salta mucho con n tan chico."], ancho=98)
    return guardar_figura(fig, "d4_linea_de_tiempo.png", destino)


def correr(out=None) -> dict:
    destino = out_dir(out)
    estilo_figuras()
    punt, cert = recorrido(False), recorrido(True)
    tau = punt["tau"]
    m_min = stats.m_min_gate(1.0, tau, DELTA)
    media_final = cert["linea_de_tiempo"][-1]["media_todas"]
    try:
        m_min_obs = stats.m_min_gate(media_final, tau, DELTA)
    except ValueError as exc:
        m_min_obs = f"no alcanzable: {exc}"
    t1, t2 = punt["tareas"]
    mismas = ([c["accion"] for t in punt["tareas"] for c in t["casos"]]
              == [c["accion"] for t in cert["tareas"] for c in t["casos"]])
    figura = _figura(punt, cert, tau, m_min, destino)
    limpiar = lambda r: {k: v for k, v in r.items() if k not in ("tareas", "tau")}  # noqa: E731
    salida = {
        "demo": "D4 — maduración sobre el caso y segunda tarea (P4)",
        "mecanismo": "MOACVAgent.advance(monitor, certified) → gate_evolution (Def. 12); "
                     "Born→Novice: una corrida TBO · Novice→Trained: training_runs = 3 · "
                     "Trained→Mature: feedback de producción",
        "gate": {"tau": tau, "delta": DELTA, "m_puntual": M_PUNTUAL,
                 "m_certificado": "todas las ventanas observadas"},
        "m_min_ventanas_perfectas": m_min,
        "media_de_todas_las_ventanas": media_final,
        "m_min_con_la_media_observada": m_min_obs,
        "puntual": limpiar(punt),
        "certificado": limpiar(cert),
        "tarea_1": _reuso(t1),
        "tarea_2_reutiliza_teorias": _reuso(t2),
        "el_estado_cambia_las_decisiones_del_matcher": not mismas,
        "puntual_retrocede_si_r_cae_bajo_tau": any(
            v["reputacion_puntual"] < tau and v["estado_despues"] != "mature"
            for v in punt["linea_de_tiempo"] if v["estado_antes"] == "mature"),
        "ventanas_en_mature_con_r_bajo_tau": [
            v["ventana"] for v in punt["linea_de_tiempo"]
            if v["estado_despues"] == "mature" and v["reputacion_puntual"] < tau],
        "figuras": [figura.name],
    }
    guardar_json(salida, "d4_maduracion.json", destino)
    return salida


def main() -> None:
    ap = argparse.ArgumentParser(description="D4 — maduración sobre el caso")
    ap.add_argument("--out", default=None, help="carpeta de salida (default docs/demos_direccion)")
    s = correr(ap.parse_args().out)
    print(f"D4 · puntual: {s['puntual']['transiciones']} · certificado: estado final "
          f"{s['certificado']['estado_final']} (m_min(1.0)={s['m_min_ventanas_perfectas']}) · "
          f"tarea 2: {s['tarea_2_reutiliza_teorias']}")


if __name__ == "__main__":
    main()
