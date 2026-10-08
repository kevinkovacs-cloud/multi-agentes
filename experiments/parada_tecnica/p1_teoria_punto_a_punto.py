#!/usr/bin/env python
"""
P1 — Un caso que genera una teoría y el agente avanzando punto a punto por el ciclo de vida
(punto 1 del pedido de la dirección; Bloque E · E2.7).

Un Semantic Matcher en Born, con la base de teorías vacía (sin warmup ni etiquetas antes de
actuar), recorre los escenarios BIO → TBO → WIO del entorno pre-registrado
(`instances/hr/entorno.py`, `configs/parada_tecnica.yaml`). En cada ciclo ejecuta las siete
regiones del LLC (`core/ciclo_llc.py`); al cierre de cada intervalo evalúa la regla de
evolución de P1 ∧ el gate de Ω.

Salidas (docs/parada_tecnica/): p1_traza_ciclo1.md (región por región del ciclo 1 y la
teoría T* que nace en R5), p1_linea_de_tiempo.png y p1.json.

Uso:  python experiments/parada_tecnica/p1_teoria_punto_a_punto.py [--out DIR]
"""
from __future__ import annotations
import argparse

from comun_pt import (C_AMBAR, C_AZUL, C_ROJO, C_TEXTO, C_VERDE, C_VIOLETA, ROTULOS,
                      cargar_config, encabezado_md, estilo_figuras, guardar_json, num,
                      out_version, pie_rotulos, plt)
from moav_hr.core.audit.trail import AuditTrail
from moav_hr.core.ciclo_llc import AgenteLLC, ConfigCiclo, MotorLLC
from moav_hr.core.monitor import FairnessMonitor
from moav_hr.core.ontology.abox import theory_iri
from moav_hr.core.theory import serialize, theory_key, violaciones_invariante_llc
from moav_hr.instances.hr import entorno
from moav_hr.instances.hr.roles_llc import RolMatcherLLC

QUE_HACE = {   # Ierache 2010, §4.2, pp. 62–63
    1: "Situación inicial: se percibe y normaliza la situación (Si).",
    2: "Acción: el planificador por ranking (Fig. 4.21) elige el plan; sin plan válido, «azar».",
    3: "Situación final: el entorno responde después de la acción (Sf).",
    4: "Utilidad: u_tarea de la acción para el resultado observado.",
    5: "Aprendizaje: registro de la teoría y ponderación de P y K (Fig. 4.13).",
    6: "Estadísticas de aprendizaje (§4.4.9).",
    7: "Evolución: se evalúa al cierre de cada intervalo (Fig. 4.28 ∧ gate de Ω).",
}


def construir(cfg: dict | None = None, version: str = "v2", nombre: str = "SemanticMatcher",
              **cambios):
    cfg = cfg or cargar_config(version=version)
    c = ConfigCiclo.desde_yaml(cfg, **cambios)
    escenarios = {capa: entorno.generar_escenario(capa, c.ciclos_por_capa[capa], cfg["semilla"])
                  for capa in entorno.CAPAS}
    agente = AgenteLLC(nombre, "matcher")
    monitor = FairnessMonitor(tau=cfg["omega"]["tau"], attr=cfg["omega"]["atributo"],
                              criterion=cfg["omega"]["criterio"],
                              disparity_threshold=cfg["omega"].get("tau_b", 0.075))
    rol = RolMatcherLLC(cfg["entorno"]["ruido_wio_epsilon"], cfg["semilla"])
    motor = MotorLLC(agente, rol, monitor, c, trail=AuditTrail(f"TRC-P1-{nombre}"))
    return cfg, c, agente, motor, escenarios


def correr_ciclo_de_vida(cfg: dict | None = None, version: str = "v2", **cambios):
    cfg, c, agente, motor, esc = construir(cfg, version, **cambios)
    res = motor.correr(esc)
    return cfg, c, agente, motor, esc, res


def _valor(v):
    return v if isinstance(v, str) else serialize(v) if isinstance(v, (dict, list)) else str(v)


def _traza_md(motor, agente, t_estrella, iri, nacimiento) -> str:
    L = encabezado_md(f"P1 · Traza región por región del ciclo 1 (pre-registro {motor.cfg.version})")
    c1 = motor.ciclos[0]
    L += [f"**Agente:** {agente.name} (rol matcher) · **estado:** {c1['estado']} · **capa:** "
          f"{c1['capa']} · **caso:** {c1['caso']['nombre']} (id {c1['caso']['id']}).", "",
          "| Región | Qué hace el LLC (Ierache 2010, §4.2) | Valores en este ciclo |",
          "|---|---|---|"]
    for ev in [e for e in motor.trail.events if e.detail.get("ciclo") == 1]:
        d = {k: v for k, v in ev.detail.items() if k not in ("ciclo", "capa", "estado")}
        valores = "; ".join(f"{k} = {_valor(v)}" for k, v in d.items())
        L.append(f"| R{ev.region} ({ev.action}) | {QUE_HACE[ev.region]} | "
                 f"{valores.replace('|', '/')} |")
    L += ["", "## La teoría T* que nace en la región 5", "",
          f"- **IRI:** `{iri}`",
          f"- **Clave:** `{serialize(list(theory_key(t_estrella, agente.theories.q)))}`",
          f"- **Al nacer (ciclo 1):** P = {nacimiento['p']}, K = {nacimiento['k']}, "
          f"U = {num(nacimiento['u'], 2)}",
          f"- **Al final de la corrida:** P = {t_estrella.p}, K = {t_estrella.k}, "
          f"U = {num(t_estrella.u, 2)}", ""]
    return "\n".join(L)


def _figura(motor, res, destino):
    import numpy as np
    ciclos = motor.ciclos
    x = np.array([r["ciclo"] for r in ciclos])
    niveles = ["Born", "Novice", "Trained", "Mature"]
    fig = plt.figure(figsize=(9, 9.2))
    a1 = fig.add_axes([0.11, 0.735, 0.86, 0.16])
    a2 = fig.add_axes([0.11, 0.475, 0.86, 0.2], sharex=a1)
    a3 = fig.add_axes([0.11, 0.19, 0.86, 0.2], sharex=a1)
    despues = {ev["ciclo"]: ev["estado_despues"] for ev in motor.evaluaciones}
    est = [niveles.index(despues.get(r["ciclo"], r["estado"])) for r in ciclos]   # tras R7
    x_max = x[-1]
    for ev in motor.evaluaciones:
        if ev["promueve"]:
            derecha = ev["ciclo"] > 0.8 * x_max
            a1.annotate(f"→ {ev['estado_despues']}", (ev["ciclo"],
                                                       niveles.index(ev["estado_despues"])),
                        xytext=(-6 if derecha else 4, 6), textcoords="offset points",
                        ha="right" if derecha else "left", fontsize=12, color=C_VERDE,
                        fontweight="bold")
    a1.step(np.r_[x[0] - 1, x], [0] + est, where="post", color=C_AZUL, lw=2.6)
    a1.set_yticks(range(4), niveles)
    a1.set_ylim(-0.85, 3.75)
    a1.set_title("Estado del agente (se gana con la regla de evolución)", fontsize=12)
    acum = [r["estadisticas"]["teorias_acumuladas"] for r in ciclos]
    a2.plot(x, acum, color=C_VIOLETA, lw=2.4, label="teorías acumuladas")
    n_iv = motor.cfg.n_intervalo
    por_iv = {}
    for r in ciclos:                                   # teorías nuevas de cada intervalo
        clave = (r["capa"], (r["ciclo_capa"] - 1) // n_iv)
        fila = por_iv.setdefault(clave, [r["ciclo"], 0])
        fila[1] += r["registro"] in ("nueva", "similar")
    nuevas_x = [v[0] + n_iv / 2 - 0.5 for v in por_iv.values()]
    a2.bar(np.array(nuevas_x), [v[1] for v in por_iv.values()], width=n_iv * 0.8,
           facecolor="none", edgecolor=C_AMBAR, hatch="//", lw=1.6,
           label=f"teorías nuevas por intervalo (n = {motor.cfg.n_intervalo})")
    a2.legend(loc="upper left", framealpha=0.95)
    a2.set_ylabel("teorías")
    ce_x = np.array([ev["ciclo"] for ev in motor.evaluaciones]) - motor.cfg.n_intervalo / 2
    w = motor.cfg.n_intervalo * 0.38
    a3.bar(ce_x - w / 2, [ev["ce_a"] for ev in motor.evaluaciones], width=w, color=C_AZUL,
           label="ciclos exitosos del agente (CE_a)")
    a3.bar(ce_x + w / 2, [ev["ce_0"] for ev in motor.evaluaciones], width=w, color=C_AMBAR,
           label="del SAR neutro, solo BIO (CE_0)")
    for ev, xx in zip(motor.evaluaciones, ce_x):
        marca = "Ω ✓" if ev["gate_omega"] else "Ω ✗"
        dato = (f"LCB {num(ev['evidencia_sesgo']['lcb'], 2)}"
                if ev.get("evidencia_sesgo") and ev["evidencia_sesgo"]["lcb"] is not None
                else f"r {num(ev['reputacion'], 2)}")
        a3.annotate(f"%CEA {num(ev['pct_cea'], 0)} %\n{dato} {marca}",
                    (xx, max(ev["ce_a"], ev["ce_0"])),
                    xytext=(0, 3), textcoords="offset points", ha="center", fontsize=12,
                    color=C_VERDE if ev["promueve"] else C_ROJO)
    tope = max([ev["ce_a"] for ev in motor.evaluaciones] + [ev["ce_0"] for ev in motor.evaluaciones]
               + [motor.cfg.n_intervalo])
    a3.set_ylim(0, tope * 1.45)
    a3.set_ylabel("ciclos exitosos" + ("\n(acumulados en la capa)"
                                        if motor.cfg.evaluacion == "acumulada_en_la_capa"
                                        else "\n(del intervalo)"))
    a3.set_xlabel("ciclo percepción–acción")
    a3.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False,
              fontsize=12, columnspacing=1.0)
    inicio = 0
    for cap in res["capas"]:
        for ax in (a1, a2, a3):
            ax.axvspan(inicio + 0.5, inicio + cap["ciclos"] + 0.5,
                       color={"BIO": "#DCE6F2", "TBO": "#E6E0F2", "WIO": "#F2E6DC"}[cap["capa"]],
                       alpha=0.5, zorder=0)
        a1.annotate(f"capa {cap['capa']}", (inicio + 1, -0.7), fontsize=12, color=C_TEXTO)
        inicio += cap["ciclos"]
    plt.setp(a1.get_xticklabels(), visible=False)
    plt.setp(a2.get_xticklabels(), visible=False)
    fig.suptitle(f"P1 ({motor.cfg.version}) · Un Matcher en Born recorre el ciclo de vida del LLC",
                 x=0.012,
                 ha="left", y=0.975, fontsize=14)
    if motor.cfg.gate == "evidencia_de_sesgo":
        txt_gate = (f"y la LCB de |Δ_DP| de la capa: Ω niega solo si LCB > τ_b = "
                    f"{num(motor.cfg.tau_b, 3)} (δ/L). CE_a y CE_0 acumulados desde el inicio "
                    "de la capa")
    else:
        txt_gate = (f"la reputación r y el gate de Ω (r ≥ τ = {num(motor.monitor.tau, 1)}). "
                    "CE_a y CE_0 del intervalo")
    pie_rotulos(fig, [
        f"Sobre cada par de barras: %CEA = 100·(CE_a − CE_0)/max(CE_0, 1), {txt_gate}. Promueve "
        f"si %CEA ≥ %RCE = {motor.cfg.rce} y Ω aprueba (verde). %TN no aplica: el agente no "
        "recibió colaboración. Bandas: escenario de cada capa."], ancho=98)
    ruta = destino / "p1_linea_de_tiempo.png"
    fig.savefig(ruta, dpi=200, facecolor="white")
    plt.close(fig)
    return ruta


def correr(out=None, version: str = "v2") -> dict:
    destino = out_version(out, version)
    estilo_figuras()
    cfg, c, agente, motor, esc, res = correr_ciclo_de_vida(version=version)
    c1 = motor.ciclos[0]
    t_estrella = next(t for t in agente.theories.theories if t.id == c1["teoria_registrada"])
    iri = str(theory_iri(agente.name, t_estrella, agente.theories.q))
    nacimiento = {"p": c1["p"], "k": c1["k"], "u": c1["u"], "ciclo": 1,
                  "registro": c1["registro"]}
    (destino / "p1_traza_ciclo1.md").write_text(
        _traza_md(motor, agente, t_estrella, iri, nacimiento), encoding="utf-8")
    fig = _figura(motor, res, destino)
    validez = [r["ciclo"] for r in motor.ciclos if r["validez_aplicada"]]
    desacuerdos = [{"ciclo": r["ciclo"], "si": r["si"], **r["desacuerdo_alg47"],
                    "candidatas": r["candidatas"]}
                   for r in motor.ciclos if r["desacuerdo_alg47"]]
    motivos = {}
    for r in motor.ciclos:
        motivos[r["motivo"]] = motivos.get(r["motivo"], 0) + 1
    usos_t = [{"ciclo": r["ciclo"], "capa": r["capa"], "estado": r["estado"],
               "como": "plan" if r["teoria_plan"] == t_estrella.id else "registro"}
              for r in motor.ciclos
              if r["teoria_plan"] == t_estrella.id or r["teoria_registrada"] == t_estrella.id]
    salida = {
        "demo": "P1 — un caso que genera una teoría y el ciclo de vida punto a punto",
        "config": {"version": c.version, "evaluacion": c.evaluacion, "gate": c.gate,
                   "utilidad_teoria": c.utilidad_teoria, "validez": c.validez,
                   "tau_b": c.tau_b, "delta_omega": c.delta_omega,
                   "n_intervalo": c.n_intervalo, "ciclos_por_capa": c.ciclos_por_capa,
                   "rce": c.rce, "rtn": c.rtn, "tau": motor.monitor.tau, "alpha": c.alpha,
                   "respaldo_similitud": c.respaldo_similitud, "semilla": cfg["semilla"],
                   "epsilon_wio": cfg["entorno"]["ruido_wio_epsilon"]},
        "resultado": {"estado_final": res["estado_final"], "ciclos": res["ciclos"],
                      "capas": res["capas"]},
        "evaluaciones": motor.evaluaciones,
        "teoria_estrella": {"id": t_estrella.id, "iri": iri, "si": t_estrella.si,
                            "a": t_estrella.a, "sf": t_estrella.sf, "nacimiento": nacimiento,
                            "final": {"p": t_estrella.p, "k": t_estrella.k, "u": t_estrella.u},
                            "usos": usos_t},
        "estadisticas_finales": res["estadisticas"],
        "regla_de_validez_aplicada": {"veces": len(validez), "ciclos": validez},
        "desacuerdos_fig421_alg47": {"veces": len(desacuerdos), "casos": desacuerdos},
        "decisiones_por_motivo": motivos,
        "invariante_sigma_p_igual_k": violaciones_invariante_llc(agente.theories) == [],
        "ciclos": [{k: r[k] for k in ("ciclo", "capa", "ciclo_capa", "estado", "si", "accion",
                                      "motivo", "es_azar", "teoria_plan", "validez_aplicada",
                                      "accion_bio", "acierto_bio", "sf", "u_tarea",
                                      "teoria_registrada", "registro", "p", "k", "u",
                                      "exitoso", "grupo")}
                   for r in motor.ciclos],
        "figuras": [fig.name], "trazas": ["p1_traza_ciclo1.md"],
    }
    guardar_json(salida, "p1.json", destino)
    return salida


def main() -> None:
    ap = argparse.ArgumentParser(description="P1 — teoría punto a punto")
    ap.add_argument("--out", default=None, help="carpeta base (se escribe en <out>/<version>)")
    ap.add_argument("--version", choices=["v1", "v2"], default="v2")
    a = ap.parse_args()
    s = correr(a.out, a.version)
    r = s["resultado"]
    print(f"P1 {a.version} · estado final {r['estado_final']} en {r['ciclos']} ciclos · capas "
          f"{[(c['capa'], c['promovido'], c['ciclos']) for c in r['capas']]} · "
          f"T* = T{s['teoria_estrella']['id']} · validez aplicada "
          f"{s['regla_de_validez_aplicada']['veces']} · desacuerdos Fig.4.21/Alg.4.7 "
          f"{s['desacuerdos_fig421_alg47']['veces']} · motivos {s['decisiones_por_motivo']}")


if __name__ == "__main__":
    main()
