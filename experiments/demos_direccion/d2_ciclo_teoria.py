#!/usr/bin/env python
"""
D2 — Ciclo de vida de una teoría: creación e iteración en dos tareas (pedido P1).

El Semantic Matcher arranca con la base VACÍA (sin warmup) y recorre dos tareas
consecutivas: la tarea 1 es el lote de 12 candidatos de la PoC; la tarea 2, el lote
determinista de tarea2.py (mismo puesto, Si repetidas). En cada caso recupera y decide
(región 2) y aprende (región 5) con learn(Si, A, Sf, acierto), sin pasar `u`.

Se sigue UNA teoría: la que el Matcher selecciona para decidir el caso de Fátima en la
tarea 1 (si ese caso no recupera ninguna, la de más usos al final). Se registra cuándo
nace y cada uso posterior con P, K, U y su puesto en el ranking de su celda de Si.
Métrica de la región 7 del LLC: teorías nuevas por tarea.

Uso:  python experiments/demos_direccion/d2_ciclo_teoria.py [--out DIR]
"""
from __future__ import annotations
import argparse

from comun import (C_AMBAR, C_AZUL, C_ROJO, C_TEXTO, C_VERDE, comas, ejecutar_tarea,
                   estilo_figuras, guardar_figura, guardar_json, num, out_dir,
                   pie_rotulos, pipeline_vacio, plt, puesto_en_celda, si_corta,
                   teoria_dict)
from tarea2 import SEMILLA, generar_tarea2_con_plantillas
from moav_hr.instances.hr.synthetic import CANDIDATES

CASO_FATIMA = 3


def correr_tareas():
    """Corre las dos tareas y devuelve (pipe, tarea1, tarea2, instantáneas, lote2)."""
    pipe = pipeline_vacio()
    base = pipe.matcher.theories
    fotos = []                                   # estado de TODAS las teorías tras cada caso

    def foto(caso, _t):
        estado = {}
        for t in base.theories:
            puesto, n = puesto_en_celda(base, t)
            estado[t.id] = {"p": t.p, "k": t.k, "u": round(t.u, 4),
                            "puesto": puesto, "n_celda": n}
        fotos.append({"tarea": caso["tarea"], "candidato_id": caso["candidato_id"],
                      "nombre": caso["nombre"], "teoria_aprendida": caso["teoria_aprendida"],
                      "acierto": caso["acierto"], "estado": estado})

    t1 = ejecutar_tarea(pipe, CANDIDATES, 1, despues_de_caso=foto)
    lote2 = generar_tarea2_con_plantillas()
    t2 = ejecutar_tarea(pipe, [c for c, _ in lote2], 2, despues_de_caso=foto)
    return pipe, t1, t2, fotos, lote2


def _elegir(t1, pipe) -> tuple[int, str]:
    caso = next(c for c in t1["casos"] if c["candidato_id"] == CASO_FATIMA)
    if caso["seleccionada"] is not None:
        return caso["seleccionada"]["id"], ("la teoría que el Matcher selecciona (★) para "
                                            "decidir el caso de Fátima en la tarea 1")
    t = max(pipe.matcher.theories.theories, key=lambda x: (x.k, -x.id))
    return t.id, "el caso de Fátima no recuperó teorías: la de más usos al final"


def _figura(seg, nuevas, destino):
    import numpy as np
    from matplotlib.ticker import MaxNLocator
    usos = seg["usos"]
    n = np.array([u["n_uso"] for u in usos], dtype=float)
    fig = plt.figure(figsize=(9, 7.8))
    a1 = fig.add_axes([0.08, 0.6, 0.58, 0.27])
    a2 = fig.add_axes([0.08, 0.3, 0.58, 0.25], sharex=a1)
    a3 = fig.add_axes([0.78, 0.3, 0.2, 0.57])
    w = 0.34
    a1.bar(n - w / 2, [u["k"] for u in usos], width=w, color=C_AZUL, label="K (usos)")
    a1.bar(n + w / 2, [u["p"] for u in usos], width=w, color=C_VERDE, label="P (aciertos)")
    for u in usos:
        a1.annotate(str(u["k"]), (u["n_uso"] - w / 2, u["k"]), xytext=(0, 3),
                    textcoords="offset points", ha="center", fontsize=12, color=C_TEXTO)
        a1.annotate(str(u["p"]), (u["n_uso"] + w / 2, u["p"]), xytext=(0, 3),
                    textcoords="offset points", ha="center", fontsize=12, color=C_TEXTO)
    kmax = max(u["k"] for u in usos)
    a1.set_ylim(0, kmax * 1.35 + 0.5)
    a1.yaxis.set_major_locator(MaxNLocator(integer=True))
    a1.set_ylabel("cantidad")
    a1.legend(loc="upper left", framealpha=0.95, ncol=2)
    a1.annotate("nace", (n[0], usos[0]["k"]), xytext=(0, 22), textcoords="offset points",
                ha="center", color=C_AMBAR, fontsize=12, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=C_AMBAR, lw=1.6))
    a2.plot(n, [u["u"] for u in usos], "-o", color=C_ROJO, lw=2.4, ms=8,
            label="U = (P+1)/(K+2)")
    for u in usos:
        a2.annotate(f"{num(u['u'], 3)}  (#{u['puesto']}/{u['n_celda']})",
                    (u["n_uso"], u["u"]), xytext=(0, -20), textcoords="offset points",
                    ha="center", fontsize=12, color=C_TEXTO)
    a2.set_ylim(0, 1.05)
    a2.set_ylabel("U")
    a2.legend(loc="upper left", framealpha=0.95)
    a2.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    comas(a2)
    corte = next((u["n_uso"] for u in usos if u["tarea"] == 2), None)
    if corte is not None:
        for ax in (a1, a2):
            ax.axvline(corte - 0.5, color=C_TEXTO, lw=1.8, ls="--")
        a2.annotate("tarea 1 | tarea 2", (corte - 0.5, 0.05), ha="center", fontsize=12,
                    color=C_TEXTO, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=C_TEXTO))
    a2.set_xticks(n, [f"uso {u['n_uso']}\n{u['nombre'].split()[0] if u['tarea'] == 1 else u['nombre'].split()[-1]}"
                      f"\ntarea {u['tarea']}" for u in usos])
    a2.set_xlim(n[0] - 0.6, n[-1] + 0.6)
    plt.setp(a1.get_xticklabels(), visible=False)
    a3.bar(["tarea 1", "tarea 2"], nuevas, color=[C_AZUL, C_VERDE], width=0.6)
    for i, v in enumerate(nuevas):
        a3.annotate(str(v), (i, v), xytext=(0, 4), textcoords="offset points",
                    ha="center", fontsize=12, color=C_TEXTO)
    a3.set_ylim(0, max(nuevas) * 1.25 + 1)
    a3.yaxis.set_major_locator(MaxNLocator(integer=True))
    a3.set_title("teorías nuevas por tarea\n(métrica de la región 7)", fontsize=12)
    fig.suptitle(f"D2 · La teoría T{seg['id']} ({seg['a']}; Si: {si_corta(seg['si'])}) "
                 "en dos tareas", x=0.012, ha="left", y=0.975, fontsize=14)
    nac = seg["nacimiento"]
    n_sel = len(seg["seleccionada_para_decidir"])
    pie_rotulos(fig, [
        f"Nace en la tarea {nac['tarea']}, caso de {nac['nombre']}, con P = {nac['p']}, "
        f"K = {nac['k']}, U = {num(nac['u'], 3)}. Un uso = el Matcher vuelve a ver esa Si, "
        "toma esa acción y observa ese resultado (learn, región 5). (#puesto/n) = puesto en "
        f"el ranking de su celda de Si (Def. 4). Además fue la seleccionada (★) para decidir "
        f"{n_sel} casos."], ancho=98)
    return guardar_figura(fig, "d2_evolucion_PKU.png", destino)


def correr(out=None) -> dict:
    destino = out_dir(out)
    estilo_figuras()
    pipe, t1, t2, fotos, lote2 = correr_tareas()
    tid, regla = _elegir(t1, pipe)
    teoria = next(t for t in pipe.matcher.theories.theories if t.id == tid)
    usos, selecciones, k_prev = [], [], 0
    for f in fotos:
        e = f["estado"].get(tid)
        if e is None:
            continue
        if e["k"] != k_prev:
            usos.append({"n_uso": e["k"], "tarea": f["tarea"], "candidato_id": f["candidato_id"],
                         "nombre": f["nombre"], "acierto": f["acierto"], **e})
            k_prev = e["k"]
    for c in t1["casos"] + t2["casos"]:
        if c["seleccionada"] is not None and c["seleccionada"]["id"] == tid:
            selecciones.append({"tarea": c["tarea"], "candidato_id": c["candidato_id"],
                                "nombre": c["nombre"], "accion": c["accion"],
                                "acierto": c["acierto"]})
    nuevas = [t1["teorias_nuevas"], t2["teorias_nuevas"]]
    seg = {"id": tid, "si": teoria.si, "a": teoria.a, "sf": teoria.sf,
           "regla_de_eleccion": regla,
           "nacimiento": {k: usos[0][k] for k in ("tarea", "candidato_id", "nombre", "p", "k", "u")},
           "usos": usos, "seleccionada_para_decidir": selecciones}
    figura = _figura(seg, nuevas, destino)

    def resumen(t):
        cs = t["casos"]
        return {"n_casos": len(cs), "teorias_nuevas": t["teorias_nuevas"],
                "casos_que_refuerzan_una_teoria_existente": len(cs) - t["teorias_nuevas"],
                "casos_con_teorias_recuperadas": sum(c["n_recuperadas"] > 0 for c in cs),
                "aciertos_del_matcher": sum(c["acierto"] for c in cs),
                "fair_w_por_ventana": [v["fair_w"] for v in t["ventanas"]]}

    salida = {
        "demo": "D2 — creación e iteración de una teoría en dos tareas (P1)",
        "convencion": {
            "base_inicial": "vacía (sin warmup): las teorías nacen en la región 5 de cada caso",
            "accion": "ADVANCE si el score del Matcher ≥ 0,75, si no REJECT (matcher_view)",
            "sf": "{'outcome': acción correcta según la calificación real del harness}",
            "acierto": "acción del Matcher == Sf['outcome']",
            "u": "learn sin `u` → U = confiabilidad de Laplace (P+1)/(K_propio+2)",
            "similitud": "token-cosine (default del código)",
        },
        "tarea_2_generador": {"modulo": "experiments/demos_direccion/tarea2.py",
                              "semilla": SEMILLA,
                              "candidatos": [{"id": c.id, "plantilla_tarea_1": pid,
                                              "gender": c.gender, "origin": c.origin,
                                              "exp": c.exp, "edu": c.edu,
                                              "skills": list(c.skills),
                                              "match_score": c.match_score,
                                              "true_qual": c.true_qual,
                                              "bias_risk": c.bias_risk}
                                             for c, pid in lote2]},
        "tarea_1": resumen(t1),
        "tarea_2": resumen(t2),
        "teorias_nuevas_por_tarea": nuevas,
        "teorias_nuevas_decrecen": nuevas[1] < nuevas[0],
        "teoria_seguida": seg,
        "base_final": [teoria_dict(t) for t in pipe.matcher.theories.theories],
        "casos": t1["casos"] + t2["casos"],
        "figuras": [figura.name],
    }
    guardar_json(salida, "d2_ciclo_teoria.json", destino)
    return salida


def main() -> None:
    ap = argparse.ArgumentParser(description="D2 — ciclo de vida de una teoría")
    ap.add_argument("--out", default=None, help="carpeta de salida (default docs/demos_direccion)")
    s = correr(ap.parse_args().out)
    seg = s["teoria_seguida"]
    print(f"D2 · teorías nuevas por tarea = {s['teorias_nuevas_por_tarea']} · "
          f"teoría seguida T{seg['id']} ({seg['a']}): {len(seg['usos'])} usos, "
          f"P/K final = {seg['usos'][-1]['p']}/{seg['usos'][-1]['k']}")


if __name__ == "__main__":
    main()
