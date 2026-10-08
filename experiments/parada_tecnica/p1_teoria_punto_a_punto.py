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
                      out_dir, pie_rotulos, plt)
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


def construir(cfg: dict | None = None, **cambios):
    cfg = cfg or cargar_config()
    c = ConfigCiclo.desde_yaml(cfg, **cambios)
    escenarios = {capa: entorno.generar_escenario(capa, c.ciclos_por_capa[capa], cfg["semilla"])
                  for capa in entorno.CAPAS}
    agente = AgenteLLC("SemanticMatcher", "matcher")
    monitor = FairnessMonitor(tau=cfg["omega"]["tau"], attr=cfg["omega"]["atributo"],
                              criterion=cfg["omega"]["criterio"])
    rol = RolMatcherLLC(cfg["entorno"]["ruido_wio_epsilon"], cfg["semilla"])
    motor = MotorLLC(agente, rol, monitor, c, trail=AuditTrail("TRC-P1"))
    return cfg, c, agente, motor, escenarios


def correr_ciclo_de_vida(cfg: dict | None = None, **cambios):
    cfg, c, agente, motor, esc = construir(cfg, **cambios)
    res = motor.correr(esc)
    return cfg, c, agente, motor, esc, res


def _valor(v):
    return v if isinstance(v, str) else serialize(v) if isinstance(v, (dict, list)) else str(v)


def _traza_md(motor, agente, t_estrella, iri, nacimiento) -> str:
    L = encabezado_md("P1 · Traza región por región del ciclo 1")
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
    est = [niveles.index(r["estado"]) for r in ciclos]
    for ev in motor.evaluaciones:
        if ev["promueve"]:
            est_x = ev["ciclo"]
            a1.annotate(f"→ {ev['estado_despues']}", (est_x, niveles.index(ev["estado_antes"])),
                        xytext=(4, 6), textcoords="offset points", fontsize=12,
                        color=C_VERDE, fontweight="bold")
    a1.step(x, est, where="post", color=C_AZUL, lw=2.6)
    a1.set_yticks(range(4), niveles)
    a1.set_ylim(-0.4, 3.4)
    a1.set_title("Estado del agente (se gana con la regla de evolución)", fontsize=12)
    acum = [r["estadisticas"]["teorias_acumuladas"] for r in ciclos]
    a2.plot(x, acum, color=C_VIOLETA, lw=2.4, label="teorías acumuladas")
    nuevas_x = [ev["ciclo"] for ev in motor.evaluaciones]
    a2.bar(np.array(nuevas_x) - motor.cfg.n_intervalo / 2,
           [ev["teorias_nuevas"] for ev in motor.evaluaciones], width=motor.cfg.n_intervalo * 0.8,
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
        a3.annotate(f"%CEA {num(ev['pct_cea'], 0)} %\nr {num(ev['reputacion'], 2)} {marca}",
                    (xx, max(ev["ce_a"], ev["ce_0"])),
                    xytext=(0, 3), textcoords="offset points", ha="center", fontsize=12,
                    color=C_VERDE if ev["promueve"] else C_ROJO)
    a3.set_ylim(0, motor.cfg.n_intervalo * 1.6)
    a3.set_ylabel("ciclos exitosos")
    a3.set_xlabel("ciclo percepción–acción")
    a3.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False,
              fontsize=12, columnspacing=1.0)
    inicio = 0
    for cap in res["capas"]:
        for ax in (a1, a2, a3):
            ax.axvspan(inicio + 0.5, inicio + cap["ciclos"] + 0.5,
                       color={"BIO": "#DCE6F2", "TBO": "#E6E0F2", "WIO": "#F2E6DC"}[cap["capa"]],
                       alpha=0.5, zorder=0)
        a1.annotate(f"capa {cap['capa']}", (inicio + 1, 3.05), fontsize=12, color=C_TEXTO)
        inicio += cap["ciclos"]
    plt.setp(a1.get_xticklabels(), visible=False)
    plt.setp(a2.get_xticklabels(), visible=False)
    fig.suptitle("P1 · Un Matcher en Born recorre el ciclo de vida del LLC", x=0.012,
                 ha="left", y=0.975, fontsize=14)
    pie_rotulos(fig, [
        f"Sobre cada par de barras: %CEA = 100·(CE_a − CE_0)/max(CE_0, 1), la reputación r y el "
        f"gate de Ω (r ≥ τ = {num(motor.monitor.tau, 1)}). Promueve si %CEA ≥ %RCE = "
        f"{motor.cfg.rce} y el gate aprueba (verde). %TN no aplica: el agente no recibió "
        "colaboración. Bandas: escenario de cada capa."], ancho=98)
    ruta = destino / "p1_linea_de_tiempo.png"
    fig.savefig(ruta, dpi=200, facecolor="white")
    plt.close(fig)
    return ruta


def correr(out=None) -> dict:
    destino = out_dir(out)
    estilo_figuras()
    cfg, c, agente, motor, esc, res = correr_ciclo_de_vida()
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
        "config": {"n_intervalo": c.n_intervalo, "ciclos_por_capa": c.ciclos_por_capa,
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
    ap.add_argument("--out", default=None)
    s = correr(ap.parse_args().out)
    r = s["resultado"]
    print(f"P1 · estado final {r['estado_final']} en {r['ciclos']} ciclos · capas "
          f"{[(c['capa'], c['promovido'], c['ciclos']) for c in r['capas']]} · "
          f"T* = T{s['teoria_estrella']['id']} · validez aplicada "
          f"{s['regla_de_validez_aplicada']['veces']} · desacuerdos Fig.4.21/Alg.4.7 "
          f"{s['desacuerdos_fig421_alg47']['veces']} · motivos {s['decisiones_por_motivo']}")


if __name__ == "__main__":
    main()
