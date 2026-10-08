#!/usr/bin/env python
"""
P3 · Equipos DAG: un equipo maduro hace madurar a otro (punto 3 del pedido; E5).

Reglas y parámetros pre-registrados antes de correr (docs/parada_tecnica/E5_PREREGISTRO.md;
sección `equipo_e5` de configs/parada_tecnica.yaml):

  · A recorre el flujo de E4 con las reglas de E5 y dona; si algún rol de A queda en Born,
    se frena y se avisa (no se fijan estados a mano);
  · B recibe colaboración de A rol por rol al nacer; B0 procesa los mismos casos sin
    compartir; BC procesa los mismos casos y coopera con C, en paralelo, cuando el rol de
    los dos está en Novice; N es el SAR neutro de L-3 (solo el operador BIO);
  · métricas por rol y equipo, cálculo literal de L-3 entre configuraciones y la figura
    p3_maduracion_equipos.png.

Salidas en docs/parada_tecnica/: p3_equipos.json, p3_equipos.md, p3_maduracion_equipos.png.

Uso:  python experiments/parada_tecnica/p3_equipos_dag.py [--out DIR]
"""
from __future__ import annotations
import argparse
import json

from comun_pt import (C_AMBAR, C_AZUL, C_ROJO, C_TEXTO, C_VERDE, cargar_config, encabezado_md,
                      estilo_figuras, guardar_json, num, out_dir, pie_rotulos, plt)
from preregistro_e5 import formulas_l3
from moav_hr.core.ciclo_llc import NOMBRE_ESTADO
from moav_hr.core.compartir_llc import compartir
from moav_hr.core.lifecycle import MaturityState
from moav_hr.instances.hr.equipo_llc import ROLES, EquipoLLC

SECCION = "equipo_e5"
ORDEN_ESTADO = ["Born", "Novice", "Trained", "Mature"]
TITULO = {"parser": "Parser", "matcher": "Semantic Matcher", "bias_auditor": "Bias Auditor",
          "explainer": "Explainer"}


# ------------------------------ compartición ------------------------------
def decisiones_equidad(motor) -> list[dict]:
    """Decisiones del agente en el plano de auditoría (resultado favorable del rol)."""
    attr = motor.cfg.attr
    return [{attr: g, "decision": "ADVANCE" if fav else "REJECT"}
            for reg in motor.ciclos for g, fav in (reg.get("equidad") or [])]


def compartir_rol(op: str, eq_d: EquipoLLC, eq_r: EquipoLLC, rol: str, comp: dict,
                  delta: float) -> dict:
    md, mr = eq_d.motores[rol], eq_r.motores[rol]
    decs = {md.agente.name: decisiones_equidad(md), mr.agente.name: decisiones_equidad(mr)}
    res = compartir(op, md.agente, mr.agente, eq_r.monitor, decs, 0, delta, mr.es_acierto,
                    a9=comp["a9"], a9_min=comp["a9_min_decisiones"],
                    a9_ambos=comp["a9_ambos_grupos"])
    omega = {n: {"lcb": o["evidencia_sesgo"]["lcb"], "brecha": o["evidencia_sesgo"]["brecha"],
                 "n_por_grupo": o["evidencia_sesgo"]["n_por_grupo"],
                 "aprueba": o["evidencia_sesgo"]["aprueba"],
                 "a9_decisiones": o.get("a9_decisiones")} for n, o in res["omega"].items()}
    return {"op": op, "rol": rol, "donante": res["donante"], "receptor": res["receptor"],
            "estados": res["estados"], "aceptada": res["aceptada"], "motivo": res["motivo"],
            "axioma": res.get("axioma"), "omega": omega, "conteo": res.get("conteo"),
            "base_receptor_antes": res["base_receptor_antes"],
            "base_receptor_despues": res.get("base_receptor_despues"),
            "base_donante": res["base_donante"],
            "invariante_receptor": res.get("invariante_receptor"),
            "invariante_donante": res.get("invariante_donante")}


# ------------------------------ métricas ------------------------------
def _fair_por_ventana(eq: EquipoLLC, rol: str) -> list[dict]:
    lecturas: dict[str, list] = {}
    if rol == "bias_auditor":
        for v in eq.ventanas:
            lecturas[v.id] = list(v.ciclo_auditor.get("equidad") or [])
    else:
        for ce in eq.casos:
            lecturas.setdefault(ce.ventana, []).extend(ce.ciclos[rol].get("equidad") or [])
    out = []
    for vid, lect in lecturas.items():
        tasas = {}
        for g in ("AR", "no-AR"):
            x = [fav for gr, fav in lect if gr == g]
            tasas[g] = sum(x) / len(x) if x else None
        if None in tasas.values():
            continue
        out.append({"ventana": vid, "fair_w": round(1 - abs(tasas["AR"] - tasas["no-AR"]), 4)})
    return out


def celdas_nunca_resueltas(motor) -> list[dict]:
    """Celdas de Si con al menos un fracaso y sin plan válido (U ≥ 0,5) al final."""
    celdas: dict = {}
    for reg in motor.ciclos:
        k = json.dumps(reg["si"], sort_keys=True, ensure_ascii=False)
        x = celdas.setdefault(k, {"si": reg["si"], "ciclos": 0, "fracasos": 0})
        x["ciclos"] += 1
        x["fracasos"] += int(not reg["exitoso"])
    out = []
    for x in celdas.values():
        orden = motor.planificador.ordenar(motor.agente.theories.applicable(x["si"]))
        valida = bool(orden) and motor.planificador.es_valida(orden[0])
        if x["fracasos"] and not valida:
            out.append(x)
    return sorted(out, key=lambda x: -x["ciclos"])


def metricas(eq: EquipoLLC) -> dict:
    out = {}
    for r in ROLES:
        m = eq.motores[r]
        por_capa: dict = {}
        for reg in m.ciclos:
            x = por_capa.setdefault(reg["capa"], {"ciclos": 0, "nuevas": 0, "exitosos": 0})
            x["ciclos"] += 1
            x["nuevas"] += reg["registro"] in ("nueva", "similar")
            x["exitosos"] += int(reg["exitoso"])
        for x in por_capa.values():
            x["pct_tn"] = round(100.0 * x["nuevas"] / x["ciclos"], 2)
        fair = _fair_por_ventana(eq, r)
        lect = [(g, f) for reg in m.ciclos for g, f in (reg.get("equidad") or [])]
        tasas = {g: (sum(f for gr, f in lect if gr == g) / max(1, sum(gr == g for gr, _ in lect)))
                 for g in ("AR", "no-AR")}
        out[r] = {
            "agente": m.agente.name, "estado_final": NOMBRE_ESTADO[m.agente.maturity.label],
            "evoluciona": getattr(eq.roles[r], "evoluciona", True),
            "ciclos": m.ciclo, "teorias": len(m.agente.theories),
            "promociones": [{"ciclo": e["ciclo"], "de": e["estado_antes"],
                             "a": e["estado_despues"]} for e in m.evaluaciones if e["promueve"]],
            "evaluaciones": [{k: e[k] for k in ("ciclo", "capa", "ciclo_capa", "ce_a", "ce_0",
                                                "pct_cea", "teorias_nuevas", "pct_tn",
                                                "tn_aplica", "gate_omega", "promueve")}
                             for e in m.evaluaciones],
            "teorias_nuevas_por_capa": por_capa,
            "ciclos_exitosos": sum(int(x["exitoso"]) for x in m.ciclos),
            "ciclos_exitosos_operador_bio": sum(int(x["acierto_bio"]) for x in m.ciclos),
            "teorias_nuevas": sum(x["registro"] in ("nueva", "similar") for x in m.ciclos),
            "fair_w": fair,
            "fair_w_media": round(sum(f["fair_w"] for f in fair) / len(fair), 4) if fair else None,
            "fair_w_min": min((f["fair_w"] for f in fair), default=None),
            "tasa_favorable": {g: round(v, 4) for g, v in tasas.items()},
            "brecha_favorable": round(abs(tasas["AR"] - tasas["no-AR"]), 4),
            "celdas_nunca_resueltas": celdas_nunca_resueltas(m),
            "motivos": _motivos(m)}
    return out


def _motivos(motor) -> dict:
    out: dict = {}
    for reg in motor.ciclos:
        out.setdefault(reg["capa"], {}).setdefault(reg["motivo"], 0)
        out[reg["capa"]][reg["motivo"]] += 1
    return out


def l3(met: dict, conf: list[str], roles: list[str]) -> dict:
    """Cálculo literal de L-3 entre configuraciones (Tablas L-16 y L-17)."""
    out = {}
    for r in roles:
        ce = {c: met[c][r]["ciclos_exitosos"] for c in conf}
        tn = {c: met[c][r]["teorias_nuevas"] for c in conf}
        ce_min, ce_prom = ce["N"], sum(ce.values()) / len(conf)
        tn_max, tn_prom = max(tn.values()), sum(tn.values()) / len(conf)
        fila = {"ciclos_exitosos": ce, "teorias_nuevas": tn, "ce_neutro": ce_min,
                "ce_promedio": round(ce_prom, 2), "tn_maximo": tn_max,
                "tn_promedio": round(tn_prom, 2),
                "neutro_es_el_minimo": ce_min == min(ce.values()), "evaluadas": {}}
        for ev in ("B", "BC"):
            f = formulas_l3(ce_min, ce[ev], ce_prom, tn_max, tn[ev], tn_prom)
            f = {k: round(v, 2) for k, v in f.items()}
            fila["evaluadas"][ev] = {**f, "es_el_maximo_de_ce": ce[ev] == max(ce.values()),
                                     "evoluciona": f["pct_cea"] >= f["pct_rce"]
                                     and f["pct_tna"] <= f["pct_rtn"]}
        out[r] = fila
    return out


def _ciclo_de(info: dict, a: str):
    return next((p["ciclo"] for p in info["promociones"] if p["a"] == a), None)


# ------------------------------ figura ------------------------------
def figura(eqs: dict, coop: dict, destino) -> str:
    estilo_figuras()
    roles = ["parser", "matcher", "explainer"]
    series = [("B0", "B0 · sin compartir", C_ROJO, 0.08, "-"),
              ("B", "B · colaboración de A al nacer", C_AZUL, 0.0, "-"),
              ("BC", "BC · cooperación con C en Novice", C_VERDE, -0.08, "--")]
    fig, axs = plt.subplots(len(roles), 1, figsize=(9, 10.2), sharex=True)
    fig.subplots_adjust(left=0.13, right=0.97, top=0.9, bottom=0.2, hspace=0.32)
    for ax, r in zip(axs, roles):
        for nombre, etiqueta, col, dy, ls in series:
            lt = eqs[nombre].linea_de_tiempo
            xs = [0] + [p["casos"] for p in lt]
            ys = [0] + [ORDEN_ESTADO.index(p["estados"][r]) for p in lt]
            # el estado cambia al cierre de la ventana: vale desde ese caso en adelante
            ax.step(xs, [y + dy for y in ys], where="post", color=col, lw=2.6, ls=ls,
                    label=etiqueta)
        c = coop.get(r, {})
        acept = next((x for x in c.get("intentos", []) if x["aceptada"]), None)
        if acept is not None:
            ax.axvline(acept["casos"], color=C_VERDE, lw=1.4, ls=":")
            ax.text(acept["casos"] + 3, 0.15, "BC coopera con C", color=C_VERDE, fontsize=12)
        ax.set_yticks(range(4))
        ax.set_yticklabels(ORDEN_ESTADO)
        ax.set_ylim(-0.4, 3.4)
        ax.set_title(TITULO[r], loc="left", fontsize=14)
        ax.grid(axis="y", color=C_TEXTO, alpha=0.15)
    axs[-1].set_xlabel("casos procesados por el equipo")
    axs[0].legend(loc="lower right", framealpha=0.95)
    fig.suptitle("Estados ganados por rol: B (colaboración de A) frente a B0 y BC",
                 x=0.012, ha="left", y=0.975, fontsize=14)
    pie_rotulos(fig, ["Mismos casos para B, B0 y BC (semilla de B). Las líneas están levemente "
                      "desplazadas en vertical para que no se tapen. El Bias Auditor no tiene "
                      "estados (E5, decisión 1)."], ancho=98)
    ruta = destino / "p3_maduracion_equipos.png"
    fig.savefig(ruta, dpi=200, facecolor="white")
    plt.close(fig)
    return ruta.name


# ------------------------------ Markdown ------------------------------
def _promos(info: dict) -> str:
    return "; ".join(f"{p['de']} → {p['a']} en el ciclo {p['ciclo']}"
                     for p in info["promociones"]) or "ninguna"


def escribir_md(res: dict, destino) -> None:
    met, conf = res["metricas"], res["config_e5"]["l3"]["configuraciones"]
    L = encabezado_md("P3 · Equipos DAG: un equipo maduro hace madurar a otro (E5)")
    L += ["Reglas pre-registradas en `docs/parada_tecnica/E5_PREREGISTRO.md`.", "",
          "## Colaboración A → B (al nacer B)", "",
          "| Rol | Estados (A → B) | Aceptada | Motivo | Iguales / similares / nuevas | "
          "Base de B (antes → después) | ΣP = K en B | LCB de Ω (A) |", "|---|---|---|---|---|---|---|---|"]
    for x in res["colaboracion"]:
        c = x["conteo"] or {}
        lcb = x["omega"][x["donante"]]["lcb"]
        L.append(f"| {TITULO[x['rol']]} | {x['estados']['donante']} → {x['estados']['receptor']} "
                 f"| {'sí' if x['aceptada'] else 'no'} | {x['motivo']} | "
                 f"{c.get('igual', '—')} / {c.get('similar', '—')} / {c.get('nueva', '—')} | "
                 f"{x['base_receptor_antes']} → {x.get('base_receptor_despues', '—')} | "
                 f"{'sí' if x.get('invariante_receptor') else '—'} | "
                 f"{'—' if lcb is None else num(lcb, 3)} |")
    L += ["", "## Cooperación BC ↔ C (en Novice, ventana a ventana)", "",
          "| Rol | Ventanas con BC en Novice (estado de C) | Intentos | Resultado |",
          "|---|---|---|---|"]
    for r, c in res["cooperacion"].items():
        esperas = ", ".join(f"{w['ventana']} ({w['estado_C']})" for w in c["bc_en_novice"]) or "ninguna"
        acept = next((x for x in c["intentos"] if x["aceptada"]), None)
        resul = ("aceptada en " + acept["ventana"] + " (iguales / similares / nuevas: "
                 + " / ".join(str(acept["conteo"][k]) for k in ("igual", "similar", "nueva"))
                 + "; ΣP = K en los dos: "
                 + ("sí" if acept["invariante_receptor"] and acept["invariante_donante"] else "no")
                 + ")") if acept else ("; ".join(x["motivo"] for x in c["intentos"])
                                       or "no coincidieron en Novice")
        L.append(f"| {TITULO[r]} | {esperas} | {len(c['intentos'])} | {resul} |")
    L += ["", "## Ciclos hasta cada cambio de estado", "",
          "| Rol | " + " | ".join(res["equipos"]) + " |", "|---|" + "---|" * len(res["equipos"])]
    for r in ROLES:
        celdas = []
        for e in res["equipos"]:
            info = met[e][r]
            celdas.append("sin estados (E5, decisión 1)" if not info["evoluciona"] and e != "N"
                          else "SAR neutro" if e == "N" else
                          f"{info['estado_final']}: {_promos(info)}")
        L.append(f"| {TITULO[r]} | " + " | ".join(celdas) + " |")
    L += ["", "## Ciclos exitosos, teorías nuevas, fair(W) y celdas nunca resueltas", "",
          "| Equipo | Rol | Ciclos exitosos | Del operador BIO (CE_0) | Teorías nuevas (por capa: "
          "nuevas / ciclos) | fair(W) media · mínimo | Brecha favorable | Celdas nunca resueltas |",
          "|---|---|---|---|---|---|---|---|"]
    for e in res["equipos"]:
        for r in ROLES:
            i = met[e][r]
            capas = ", ".join(f"{c} {x['nuevas']}/{x['ciclos']}"
                              for c, x in i["teorias_nuevas_por_capa"].items())
            fw = ("—" if i["fair_w_media"] is None else
                  f"{num(i['fair_w_media'], 3)} · {num(i['fair_w_min'], 3)}")
            nr = "; ".join(f"{' · '.join(str(v) for v in x['si'].values())} "
                           f"({x['fracasos']}/{x['ciclos']})"
                           for x in i["celdas_nunca_resueltas"]) or "ninguna"
            L.append(f"| {e} | {TITULO[r]} | {i['ciclos_exitosos']} | "
                     f"{i['ciclos_exitosos_operador_bio']} | {capas} | {fw} | "
                     f"{num(i['brecha_favorable'], 3)} | {nr} |")
    L += ["", "## Cálculo literal de L-3 entre configuraciones", "",
          "En la tesis, los porcentajes se determinan comparando configuraciones de SAR (Anexo "
          "L-3, Tablas L-16 y L-17). Para decidir la promoción de un agente individual durante su "
          "actuación se operacionalizan como en P1; acá se calculan como en la fuente, entre "
          f"configuraciones que procesan los mismos casos ({', '.join(conf)}; mínimo = el "
          "neutro N).", "",
          "| Rol | Ciclos exitosos (" + ", ".join(conf) + ") | Teorías nuevas (" + ", ".join(conf)
          + ") | Evaluada | %CEA | %RCE | %TNA | %RTN | Evoluciona |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r, f in res["l3"].items():
        for ev, x in f["evaluadas"].items():
            L.append(f"| {TITULO[r]} | " + ", ".join(str(f["ciclos_exitosos"][c]) for c in conf)
                     + " | " + ", ".join(str(f["teorias_nuevas"][c]) for c in conf)
                     + f" | {ev} | {num(x['pct_cea'], 1)} | {num(x['pct_rce'], 1)} | "
                     f"{num(x['pct_tna'], 1)} | {num(x['pct_rtn'], 1)} | "
                     f"{'sí' if x['evoluciona'] else 'no'} |")
    L += ["", "**Nota técnica para conversar con Jorge.** Con estas definiciones, %TNA ≤ %RTN "
          "equivale a «promedio de teorías nuevas ≤ máximo», y %CEA ≥ %RCE equivale a «ciclos "
          "exitosos de la configuración evaluada ≥ promedio de las configuraciones».", "",
          f"![Estados por rol]({res['figura']})", ""]
    (destino / "p3_equipos.md").write_text("\n".join(L) + "\n", encoding="utf-8")


# ------------------------------ corrida ------------------------------
def correr(out=None) -> dict:
    cfg = cargar_config()
    destino = out_dir(out)
    e5 = cfg["equipo_e5"]
    S, comp, delta = e5["equipos"], e5["compartir_e5"], cfg["omega"]["delta"]
    eqs = {"A": EquipoLLC("A", cfg, SECCION, S["A"])}
    eqs["A"].correr()
    faltan = [r for r in comp["roles"] if eqs["A"].agentes[r].maturity == MaturityState.BORN]
    if faltan:                                               # pre-registro: detener y avisar
        res = {"detenido": True, "motivo": "roles de A en Born: " + ", ".join(faltan),
               "estados_A": eqs["A"].estados()}
        guardar_json(res, "p3_equipos.json", destino)
        return res
    eqs["B"] = EquipoLLC("B", cfg, SECCION, S["B"])
    colaboracion = []
    for r in comp["roles"]:                                  # A → B, rol por rol, al nacer B
        x = compartir_rol("colaboracion", eqs["A"], eqs["B"], r, comp, delta)
        if x["aceptada"]:
            eqs["B"].motores[r].recibio_colaboracion[eqs["B"].agentes[r].layer.value] = True
        colaboracion.append(x)
    eqs["B"].correr()
    eqs["B0"] = EquipoLLC("B0", cfg, SECCION, S["B0"])
    eqs["B0"].correr()
    eqs["N"] = EquipoLLC("N", cfg, SECCION, S["N"], neutro=True)
    eqs["N"].correr()
    eqs["BC"], eqs["C"] = (EquipoLLC("BC", cfg, SECCION, S["BC"]),
                           EquipoLLC("C", cfg, SECCION, S["C"]))
    coop = {r: {"bc_en_novice": [], "intentos": [], "coopero": False} for r in comp["roles"]}
    for vbc, vc in zip(eqs["BC"].ventanas_del_flujo(), eqs["C"].ventanas_del_flujo()):
        eqs["BC"].procesar_ventana(vbc)
        eqs["C"].procesar_ventana(vc)
        for r in comp["roles"]:
            if coop[r]["coopero"] or eqs["BC"].agentes[r].maturity != MaturityState.NOVATO:
                continue
            est_c = eqs["C"].agentes[r].maturity
            coop[r]["bc_en_novice"].append({"ventana": vbc.id,
                                            "estado_C": NOMBRE_ESTADO[est_c.label]})
            if est_c != MaturityState.NOVATO:
                continue
            x = compartir_rol("cooperacion", eqs["BC"], eqs["C"], r, comp, delta)
            x.update(ventana=vbc.id, casos=len(eqs["BC"].casos))
            coop[r]["intentos"].append(x)
            coop[r]["coopero"] = x["aceptada"]
    orden = ["A", "B", "B0", "BC", "C", "N"]
    met = {e: metricas(eqs[e]) for e in orden}
    res = {"config_e5": {k: e5[k] for k in ("auditor_evoluciona", "explora_en_wio",
                                             "si_explainer", "equipos", "compartir_e5", "l3")},
           "equipos": orden, "colaboracion": colaboracion, "cooperacion": coop,
           "metricas": met, "l3": l3(met, e5["l3"]["configuraciones"], e5["l3"]["roles"]),
           "lineas_de_tiempo": {e: eqs[e].linea_de_tiempo for e in orden},
           "b_antes_que_b0": {r: {"B": {a: _ciclo_de(met["B"][r], a) for a in ORDEN_ESTADO[1:]},
                                  "B0": {a: _ciclo_de(met["B0"][r], a) for a in ORDEN_ESTADO[1:]}}
                              for r in comp["roles"]}}
    res["figura"] = figura(eqs, coop, destino)
    guardar_json(res, "p3_equipos.json", destino)
    escribir_md(res, destino)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None)
    r = correr(ap.parse_args().out)
    if r.get("detenido"):
        print("DETENIDO:", r["motivo"])
    else:
        print(json.dumps({"estados": {e: {ro: r["metricas"][e][ro]["estado_final"] for ro in ROLES}
                                      for e in r["equipos"]},
                          "b_antes_que_b0": r["b_antes_que_b0"]}, ensure_ascii=False, indent=1))
