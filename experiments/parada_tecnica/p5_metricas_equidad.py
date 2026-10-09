#!/usr/bin/env python
"""
P5 · Métricas de equidad por rol (punto 5 del pedido; E6). Reglas y parámetros pre-registrados
antes de correr (docs/parada_tecnica/E6_PREREGISTRO.md; sección `equipo_e6` de la config).

  · Corrida 1: el equipo de E5 sobre el flujo de A extendido a 600 casos, con α = 1 y α = 0,5
    lado a lado. Métricas de equidad de cada rol (sección 6 del handoff), ê(t) por teoría,
    cuántas teorías llegan a m_min, y en cuántas planificaciones α = 0,5 cambió la elección
    respecto de α = 1 (contrafáctico dentro de la misma corrida).
  · Corrida 2: condición con sesgo programado («parámetros programados»; regla 11 del
    entorno): el Matcher solo con el rasgo proxy `titulo_local` y su operador BIO sesgado, en
    dos magnitudes; neutro, α = 1 y α = 0,5; las dos reglas del Auditor, el gate de evolución,
    la compartición y la atenuación por aprendizaje.

Salidas en docs/parada_tecnica/: p5_metricas_equidad.json, p5_sesgo_programado.json y
p5_sesgo_programado.png. METRICAS_EQUIDAD_POR_ROL.md lo escribe metricas_equidad_doc.py
(E7), con E6, E6 v2 y el control post hoc.

Uso:  python experiments/parada_tecnica/p5_metricas_equidad.py [--out DIR]
"""
from __future__ import annotations
import argparse
import json

from comun_pt import (C_AMBAR, C_AZUL, C_ROJO, C_TEXTO, C_VERDE, cargar_config,
                      estilo_figuras, guardar_json, mayus, num, out_dir,
                      pie_rotulos, plt)
from moav_hr.core import fairness
from moav_hr.core.audit.trail import AuditTrail
from moav_hr.core.ciclo_llc import NOMBRE_ESTADO, AgenteLLC, ConfigCiclo, MotorLLC
from moav_hr.core.compartir_llc import compartir
from moav_hr.core.equidad_roles import (auditar_flujo, brecha_favorable, e_por_teoria,
                                        odds_igualadas)
from moav_hr.core.monitor import FairnessMonitor
from moav_hr.instances.hr import entorno
from moav_hr.instances.hr.equipo_llc import ROLES, EquipoLLC
from moav_hr.instances.hr.roles_llc import RolMatcherSesgo, RolNeutro

SECCION = "equipo_e6"
ROTULO_PROG = "parámetros programados"
ROTULO_IV = "ilustra el mecanismo; no es evidencia de la conjetura de atenuación"
TITULO = {"parser": "Parser", "matcher": "Semantic Matcher", "bias_auditor": "Bias Auditor",
          "explainer": "Explainer"}


# ------------------------------ corrida 1 ------------------------------
def _por_ventana(eq: EquipoLLC, rol: str) -> list[dict]:
    if rol == "bias_auditor":
        grupos = [(v.id, list(v.ciclo_auditor.get("equidad") or [])) for v in eq.ventanas]
    else:
        d: dict = {}
        for ce in eq.casos:
            d.setdefault(ce.ventana, []).extend(ce.ciclos[rol].get("equidad") or [])
        grupos = list(d.items())
    return [{"ventana": vid, **brecha_favorable(lect)} for vid, lect in grupos]


def _teorias(motor, m_min: int) -> dict:
    ts = e_por_teoria(motor.registro_e, m_min)
    con_e = [t for t in ts if t["e"] is not None]
    return {"en_E": len(ts), "llegan_a_m_min": len(con_e),
            "e_min": min((t["e"] for t in con_e), default=None),
            "e_media": round(sum(t["e"] for t in con_e) / len(con_e), 4) if con_e else None,
            "teorias_con_e": con_e}


def _cambios_alpha(motor) -> dict:
    """Planificaciones en que α = 0,5 eligió otra teoría que α = 1 en el mismo estado. No
    cuentan los ciclos en que actúa una regla (Bias Auditor, DE-6): ahí el planificador no
    decide la acción."""
    regs = [r for r in motor.ciclos if "plan_alpha_1" in r
            and r["motivo"] not in ("regla_certificada", "operador_bio")]
    cambios = [r for r in regs if r["plan_alpha_1"] is not None
               and (r["plan_alpha_1"]["accion"] != r["accion"]
                    or r["plan_alpha_1"]["teoria"] != r["teoria_plan"])]
    ejemplos = [{"ciclo": r["ciclo"], "capa": r["capa"], "si": r["si"],
                 "elegida": {"accion": r["accion"], "teoria": r["teoria_plan"],
                             "motivo": r["motivo"]},
                 "con_alpha_1": r["plan_alpha_1"],
                 "candidatas": [{k: c[k] for k in ("id", "a", "sf", "u_tarea", "u_orden", "e")}
                                for c in r["candidatas"]]} for r in cambios[:3]]
    def e_de(r, tid):
        return next((c["e"] for c in r["candidatas"] if c["id"] == tid), None)
    sin_e = sum(1 for r in cambios if e_de(r, r["teoria_plan"]) is None
                and e_de(r, r["plan_alpha_1"]["teoria"]) is not None)
    return {"planificaciones": len(regs),
            "equidad_usada": sum(bool(r.get("equidad_usada")) for r in regs),
            "eleccion_cambiada": len(cambios),
            "accion_cambiada": sum(r["plan_alpha_1"]["accion"] != r["accion"] for r in cambios),
            "elegida_sin_e_frente_a_una_con_e": sin_e,
            "ejemplos": ejemplos}


def metricas_equipo(eq: EquipoLLC, m_min: int) -> dict:
    out = {}
    for r in ROLES:
        m = eq.motores[r]
        lect = [(g, f) for reg in m.ciclos for g, f in (reg.get("equidad") or [])]
        fila = {"estado_final": NOMBRE_ESTADO[m.agente.maturity.label], "ciclos": m.ciclo,
                "aciertos": sum(int(x["exitoso"]) for x in m.ciclos),
                "favorable": brecha_favorable(lect), "por_ventana": _por_ventana(eq, r),
                "teorias": _teorias(m, m_min)}
        if eq.eq["alpha"] < 1.0:
            fila["alpha_0_5"] = _cambios_alpha(m)
        out[r] = fila
    mm = eq.motores["matcher"].ciclos
    out["matcher"]["odds_igualadas"] = odds_igualadas(
        [(x["grupo"], x["accion"] == "ADVANCE", bool(x["sf"]["calificado"])) for x in mm])
    out["matcher"]["odds_igualadas_por_ventana"] = []
    d: dict = {}
    for ce in eq.casos:
        x = ce.ciclos["matcher"]
        d.setdefault(ce.ventana, []).append((ce.grupo, x["accion"] == "ADVANCE",
                                            bool(x["sf"]["calificado"])))
    for vid, trios in d.items():
        out["matcher"]["odds_igualadas_por_ventana"].append({"ventana": vid,
                                                             **odds_igualadas(trios)})
    out["matcher"]["aciertos_por_grupo"] = brecha_favorable(
        [(x["grupo"], bool(x["exitoso"])) for x in mm])
    out["parser"]["dtv_canal_proxy"] = fairness.dtv_lower_bound(
        [ce.si_parser for ce in eq.casos], [ce.grupo for ce in eq.casos])
    primeros = [ce for ce in eq.casos][:260]
    out["matcher"]["primeros_260"] = {
        "advance": sum(ce.ciclos["matcher"]["accion"] == "ADVANCE" for ce in primeros),
        "aciertos_por_grupo": brecha_favorable(
            [(ce.grupo, bool(ce.ciclos["matcher"]["exitoso"])) for ce in primeros]),
        "paridad_demografica": brecha_favorable(
            [(ce.grupo, ce.ciclos["matcher"]["accion"] == "ADVANCE") for ce in primeros]),
        "odds_igualadas": odds_igualadas(
            [(ce.grupo, ce.ciclos["matcher"]["accion"] == "ADVANCE",
              bool(ce.ciclos["matcher"]["sf"]["calificado"])) for ce in primeros])}
    return out


def corrida_1(cfg: dict) -> dict:
    e6 = cfg["equipo_e6"]
    m_min = cfg["utilidad"]["m_min_por_grupo"]
    res = {}
    for a in e6["equipo_equidad"]["alphas"]:
        eq = EquipoLLC(f"E6-alfa{a}", cfg, SECCION, e6["equipo_equidad"]["semillas"], alpha=a)
        eq.correr()
        res[f"alpha_{a}"] = {"alpha": a, "casos": len(eq.casos), "ventanas": len(eq.ventanas),
                             "estados": eq.estados(), "roles": metricas_equipo(eq, m_min)}
    return res


# ------------------------------ corrida 2 ------------------------------
def flujo_sesgo(cfg: dict, p_local: dict) -> list:
    e6, sp = cfg["equipo_e6"], cfg["equipo_e6"]["sesgo_programado"]
    casos = [c for capa in ("BIO", "TBO", "WIO")
             for c in entorno.generar_escenario(capa, e6["flujo_casos"][capa], sp["semilla_casos"])]
    return entorno.asignar_titulo_local(casos, p_local, sp["semilla_rasgo"])


def _monitor(cfg: dict) -> FairnessMonitor:
    om = cfg["omega"]
    return FairnessMonitor(tau=om["tau"], attr=om["atributo"], criterion=om["criterio"],
                           disparity_threshold=om["tau_b"])


def _tasa(regs, g, pred) -> float:
    x = [pred(r) for r in regs if r["grupo"] == g]
    return sum(x) / len(x) if x else 0.0


def correr_matcher(cfg: dict, casos: list, nombre: str, conf: str,
                   equidad: str = "variante", rol=None):
    """El Matcher solo sobre los casos. `equidad` = «celda» es la E6 v2; `rol` permite el
    control post hoc (el Matcher de P1, sin rasgo ni sesgo)."""
    sp = cfg["equipo_e6"]["sesgo_programado"]
    if rol is None:
        rol = RolMatcherSesgo(cfg["entorno"]["ruido_wio_epsilon"], sp["semilla_casos"])
    if conf == "neutro":
        rol = RolNeutro(rol)
    c = ConfigCiclo.desde_yaml(cfg, alpha=0.5 if conf == "alpha_0_5" else 1.0,
                               equidad_utilidad=equidad)
    motor = MotorLLC(AgenteLLC(nombre, "matcher"), rol, _monitor(cfg), c,
                     trail=AuditTrail(f"TRC-{nombre}"))
    for caso in casos:
        motor.paso(caso)
    return motor


def metricas_sesgo(cfg: dict, motor, casos: list) -> dict:
    sp, om = cfg["equipo_e6"]["sesgo_programado"], cfg["omega"]
    attr, w = om["atributo"], sp["auditor"]["ventana"]
    regs = motor.ciclos
    ventanas = [{"id": f"W{k // w + 1:02d}", "capa": regs[k + w - 1]["capa"],
                 "registros": [{attr: r["grupo"], "decision": r["accion"]}
                               for r in regs[k:k + w]]} for k in range(0, len(regs), w)]
    aud = auditar_flujo(ventanas, motor.monitor, sp["auditor"]["acumulada"]["L"],
                        sp["auditor"]["acumulada"]["delta"])
    por_ventana = []
    for k, v in enumerate(ventanas):
        x = regs[k * w:(k + 1) * w]
        adv = lambda r: r["accion"] == "ADVANCE"  # noqa: E731
        por_ventana.append({
            "id": v["id"], "capa": v["capa"],
            "brecha_firmada": round(_tasa(x, "AR", adv) - _tasa(x, "no-AR", adv), 4),
            "accion_igual_al_operador": round(sum(r["accion"] == r["accion_bio"] for r in x)
                                              / len(x), 4),
            "actua_el_operador": round(sum(r["motivo"] in ("azar_bio", "operador_bio")
                                           for r in x) / len(x), 4),
            "deriva_ventana": aud[k]["deriva_ventana"],
            "deriva_acumulada": aud[k]["deriva_acumulada"],
            "lcb_acumulada": aud[k]["lcb_acumulada"]})
    tercio = len(regs) // 3

    def brecha(segmento):
        return round(_tasa(segmento, "AR", lambda r: r["accion"] == "ADVANCE")
                     - _tasa(segmento, "no-AR", lambda r: r["accion"] == "ADVANCE"), 4)
    m_min = cfg["utilidad"]["m_min_por_grupo"]
    teorias = _teorias(motor, m_min)
    no_local = [t for t in e_por_teoria(motor.registro_e, m_min)
                if '"titulo_local": false' in t["clave"][0]]
    out = {"estado_final": NOMBRE_ESTADO[motor.agente.maturity.label],
           "brecha_toda_la_corrida": brecha(regs),
           "brecha_por_tercio": [brecha(regs[:tercio]), brecha(regs[tercio:2 * tercio]),
                                 brecha(regs[2 * tercio:])],
           "odds_igualadas": odds_igualadas([(r["grupo"], r["accion"] == "ADVANCE",
                                              bool(r["sf"]["calificado"])) for r in regs]),
           "aciertos_por_grupo": brecha_favorable([(r["grupo"], bool(r["exitoso"]))
                                                   for r in regs]),
           "por_ventana": por_ventana,
           "ventanas_derivadas_regla_ventana": [v["id"] for v in por_ventana
                                                if v["deriva_ventana"]],
           "ventanas_derivadas_regla_acumulada": [v["id"] for v in por_ventana
                                                  if v["deriva_acumulada"]],
           "evolucion": [{k: e[k] for k in ("ciclo", "capa", "ciclo_capa", "pct_cea",
                                             "gate_omega", "promueve", "estado_despues")}
                         | {"lcb": (e.get("evidencia_sesgo") or {}).get("lcb"),
                            "brecha": (e.get("evidencia_sesgo") or {}).get("brecha"),
                            "niega_omega": (e.get("evidencia_sesgo") or {}).get("niega")}
                         for e in motor.evaluaciones],
           "teorias": {k: v for k, v in teorias.items() if k != "teorias_con_e"},
           "teorias_sin_titulo_local": {
               "en_E": len(no_local),
               "llegan_a_m_min": sum(t["e"] is not None for t in no_local),
               "lecturas_AR": sum(t["n_por_grupo"].get("AR", 0) for t in no_local),
               "lecturas_no_AR": sum(t["n_por_grupo"].get("no-AR", 0) for t in no_local)}}
    if motor.cfg.alpha < 1.0:
        out["alpha_0_5"] = _cambios_alpha(motor)
    return out


def comparticion(cfg: dict, donante) -> dict:
    sp = cfg["equipo_e6"]["sesgo_programado"]
    attr = cfg["omega"]["atributo"]
    receptor = correr_matcher(cfg, [], f"{donante.agente.name}-receptor", "alpha_1")
    decs = {donante.agente.name: [{attr: r["grupo"], "decision": r["accion"]}
                                  for r in donante.ciclos],
            receptor.agente.name: []}
    r = compartir("colaboracion", donante.agente, receptor.agente, donante.monitor, decs, 0,
                  sp["auditor"]["acumulada"]["delta"], receptor.es_acierto,
                  a9=sp["comparticion"]["a9"])
    ev = r["omega"][donante.agente.name]["evidencia_sesgo"]
    return {"donante": donante.agente.name, "estados": r["estados"], "aceptada": r["aceptada"],
            "motivo": r["motivo"], "axioma": r.get("axioma"),
            "omega_donante": {"brecha": ev["brecha"], "lcb": ev["lcb"], "niega": ev["niega"],
                              "n_por_grupo": ev["n_por_grupo"]},
            "conteo": r.get("conteo")}


def calificados_del_flujo(cfg: dict) -> dict:
    """Tasa de calificados por grupo en el flujo de 600 casos (entorno, sin agentes): la tasa
    base contra la que se lee la paridad demográfica de las dos corridas."""
    casos = flujo_sesgo(cfg, {"AR": 0.5, "no-AR": 0.5})
    return brecha_favorable([(c.grupo, c.calificado) for c in casos])


def corrida_2(cfg: dict) -> dict:
    sp = cfg["equipo_e6"]["sesgo_programado"]
    res = {}
    for mag, p in sp["magnitudes"].items():
        casos = flujo_sesgo(cfg, p)
        fila = {"p_local": p, "brecha_operador_esperada": round(
            entorno.brecha_operador_sesgado(p), 4),
            "dtv_si_matcher": fairness.dtv_lower_bound(
                [RolMatcherSesgo(0.1, 0).percibir(c) for c in casos], [c.grupo for c in casos]),
            "configuraciones": {}}
        for conf in sp["configuraciones"]:
            motor = correr_matcher(cfg, casos, f"Matcher-{mag}-{conf}", conf)
            x = metricas_sesgo(cfg, motor, casos)
            if conf != "neutro":
                x["comparticion"] = comparticion(cfg, motor)
            fila["configuraciones"][conf] = x
        res[mag] = fila
    return res


# ------------------------------ figura y documento ------------------------------
def figura(c2: dict, base: dict, destino) -> str:
    estilo_figuras()
    series = [("neutro", "neutro (solo el operador sesgado)", C_TEXTO, ":"),
              ("alpha_1", "Matcher que aprende, α = 1", C_AZUL, "-"),
              ("alpha_0_5", "Matcher que aprende, α = 0,5", C_VERDE, "--")]
    mags = list(c2)
    fig, axs = plt.subplots(len(mags), 1, figsize=(9, 9.6), sharex=True)
    fig.subplots_adjust(left=0.12, right=0.97, top=0.9, bottom=0.2, hspace=0.35)
    for ax, mag in zip(axs, mags):
        for j, (conf, etiqueta, col, ls) in enumerate(series):
            pv = c2[mag]["configuraciones"][conf]["por_ventana"]
            xs = list(range(1, len(pv) + 1))
            ax.plot(xs, [v["brecha_firmada"] for v in pv], color=col, lw=2.4, ls=ls,
                    label=etiqueta)
            der = [i + 1 for i, v in enumerate(pv) if v["deriva_acumulada"]]
            ax.scatter(der, [0.92 - 0.08 * j] * len(der), marker="v", s=60, color=col,
                       zorder=3)
        ax.axhline(0, color=C_TEXTO, lw=1)
        ax.axhline(c2[mag]["brecha_operador_esperada"], color=C_ROJO, lw=1.4, ls="--")
        ax.axhline(base["tasas"]["AR"] - base["tasas"]["no-AR"], color=C_AMBAR, lw=1.4,
                   ls="-.")
        ax.set_ylim(-0.6, 1.0)
        ax.set_ylabel("tasa ADVANCE AR − no-AR")
        ax.set_title(f"Magnitud {mag.replace('_', ' ')}: brecha del operador "
                     f"{num(c2[mag]['brecha_operador_esperada'], 2)} (línea roja)", loc="left",
                     fontsize=14)
        ax.grid(color=C_TEXTO, alpha=0.15)
    axs[-1].set_xlabel("ventana de 20 decisiones")
    axs[0].legend(loc="lower right", framealpha=0.95)
    fig.suptitle("Sesgo programado por un proxy: brecha por ventana y derivaciones",
                 x=0.012, ha="left", y=0.975, fontsize=14)
    iguales = all(c2[m]["configuraciones"]["alpha_1"]["por_ventana"]
                  == c2[m]["configuraciones"]["alpha_0_5"]["por_ventana"] for m in mags)
    pie_rotulos(fig, [mayus(ROTULO_PROG) + ". Línea roja: brecha del operador sesgado; línea "
                      "ámbar: diferencia de calificados entre grupos en el flujo (tasa base). "
                      "Triángulos: ventanas que deriva la regla acumulada (ii); la regla de "
                      "ventana (i) no deriva ninguna."
                      + (" Las curvas de α = 1 y α = 0,5 coinciden: mismas decisiones." if iguales
                         else "") + " Atenuación: " + ROTULO_IV + "."], ancho=98)
    ruta = destino / "p5_sesgo_programado.png"
    fig.savefig(ruta, dpi=200, facecolor="white")
    plt.close(fig)
    return ruta.name


def correr(out=None) -> dict:
    cfg = cargar_config()
    destino = out_dir(out)
    c1 = corrida_1(cfg)
    guardar_json({"demo": "P5 · corrida 1: equidad por rol, α = 1 y α = 0,5",
                  "calificados_del_flujo": calificados_del_flujo(cfg), **c1},
                 "p5_metricas_equidad.json", destino)
    c2 = corrida_2(cfg)
    base = calificados_del_flujo(cfg)
    fig = figura(c2, base, destino)
    guardar_json({"demo": "P5 · corrida 2: sesgo programado por un proxy",
                  "rotulo_programado": ROTULO_PROG, "rotulo_atenuacion": ROTULO_IV,
                  "calificados_del_flujo": base,
                  "figura": fig, **c2}, "p5_sesgo_programado.json", destino)
    return {"corrida_1": c1, "corrida_2": c2}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None)
    r = correr(ap.parse_args().out)
    resumen = {k: {"estados": v["estados"], **{ro: {"brecha": v["roles"][ro]["favorable"]["brecha"],
                                                    "m_min": v["roles"][ro]["teorias"]["llegan_a_m_min"]}
                                               for ro in ROLES}}
               for k, v in r["corrida_1"].items()}
    print(json.dumps(resumen, ensure_ascii=False, indent=1))
    for mag, f in r["corrida_2"].items():
        for conf, x in f["configuraciones"].items():
            print(mag, conf, x["estado_final"], x["brecha_toda_la_corrida"], x["brecha_por_tercio"],
                  "deriva(i)", len(x["ventanas_derivadas_regla_ventana"]),
                  "deriva(ii)", x["ventanas_derivadas_regla_acumulada"][:5],
                  x.get("comparticion", {}).get("aceptada"))
