#!/usr/bin/env python
"""
E6 v2 · La equidad por celda (Si, A) en la utilidad (E6_RESPUESTA, decisión 1; pre-registro
corto en docs/parada_tecnica/E6_PREREGISTRO_v2.md). Vuelve a correr solo lo que toca
α = 0,5: la corrida 1 (el equipo de E5 sobre los 600 casos) y la condición con sesgo
programado, con ê(Si, A). Las corridas con α = 1 y el neutro se toman de E6
(p5_metricas_equidad.json y p5_sesgo_programado.json), que no cambian.

Salidas en docs/parada_tecnica/: p5_equidad_v2.json y p5_equidad_v2.md (v1 y v2 lado a lado).

Uso:  python experiments/parada_tecnica/p5_equidad_v2.py [--out DIR]
"""
from __future__ import annotations
import argparse
import json

from comun_pt import cargar_config, encabezado_md, guardar_json, num, out_dir
from p5_metricas_equidad import (ROTULO_PROG, TITULO, correr_matcher, flujo_sesgo,
                                 metricas_equipo, metricas_sesgo)
from moav_hr.instances.hr.equipo_llc import EquipoLLC

SECCION = "equipo_e6_v2"
ROLES_PLAN = ("parser", "matcher", "explainer")


def _ajuste(motor) -> dict:
    regs = [r for r in motor.ciclos if "ajuste_equidad" in r
            and r["motivo"] not in ("regla_certificada", "operador_bio")]
    return {"planificaciones": len(regs),
            "con_candidatas": sum(r["ajuste_equidad"] is not None for r in regs),
            "aplicado": sum(r["ajuste_equidad"] == "aplicado" for r in regs),
            "no_aplicable_falta_evidencia": sum(
                r["ajuste_equidad"] == "no aplicable: falta evidencia" for r in regs)}


def corrida_1_v2(cfg: dict) -> dict:
    v2 = cfg[SECCION]
    m_min = cfg["utilidad"]["m_min_por_grupo"]
    eq = EquipoLLC("E6v2-alfa0.5", cfg, SECCION, cfg["equipo_e6"]["equipo_equidad"]["semillas"],
                   alpha=0.5)
    eq.correr()
    roles = metricas_equipo(eq, m_min)
    for r in ROLES_PLAN:
        roles[r]["ajuste_v2"] = _ajuste(eq.motores[r])
    return {"alpha": 0.5, "equidad_utilidad": v2["equidad_utilidad"], "casos": len(eq.casos),
            "estados": eq.estados(), "roles": roles}


def corrida_2_v2(cfg: dict) -> dict:
    sp = cfg["equipo_e6"]["sesgo_programado"]
    out = {}
    for mag, p in sp["magnitudes"].items():
        casos = flujo_sesgo(cfg, p)
        motor = correr_matcher(cfg, casos, f"Matcher-{mag}-alpha_0_5-v2", "alpha_0_5",
                               equidad="celda")
        x = metricas_sesgo(cfg, motor, casos)
        x["ajuste_v2"] = _ajuste(motor)
        out[mag] = x
    return out


def _acc_eo(roles: dict) -> dict:
    m = roles["matcher"]
    return {"aciertos_matcher": m["aciertos"], "aciertos_por_grupo": m["aciertos_por_grupo"],
            "eo": m["odds_igualadas"], "paridad_demografica": m["favorable"]["brecha"]}


def escribir_md(res: dict, destino) -> None:
    v1 = json.loads((destino / "p5_metricas_equidad.json").read_text(encoding="utf-8"))
    s1 = json.loads((destino / "p5_sesgo_programado.json").read_text(encoding="utf-8"))
    c1 = res["corrida_1"]
    L = encabezado_md("E6 v2 · Equidad por celda (Si, A): v1 y v2 lado a lado")
    L += ["Pre-registro corto: `E6_PREREGISTRO_v2.md`. Se volvió a correr solo lo que toca "
          "α = 0,5; las corridas con α = 1 y el neutro son las de E6.", "",
          "## Corrida 1: el equipo de E5 sobre los 600 casos", "",
          "| Rol | Ajuste v2: aplicado · no aplicable por falta de evidencia (de las "
          "planificaciones con candidatas) | Cambios de teoría frente a α = 1 (v1 · v2) | "
          "Cambios de acción (v1 · v2) | Aciertos (α = 1 · v1 · v2) |", "|---|---|---|---|---|"]
    for r in ROLES_PLAN:
        a_v1 = v1["alpha_0.5"]["roles"][r]["alpha_0_5"]
        a_v2 = c1["roles"][r]["alpha_0_5"]
        aj = c1["roles"][r]["ajuste_v2"]
        L.append(f"| {TITULO[r]} | {aj['aplicado']} · {aj['no_aplicable_falta_evidencia']} (de "
                 f"{aj['con_candidatas']}) | {a_v1['eleccion_cambiada']} · "
                 f"{a_v2['eleccion_cambiada']} | {a_v1['accion_cambiada']} · "
                 f"{a_v2['accion_cambiada']} | {v1['alpha_1.0']['roles'][r]['aciertos']} · "
                 f"{v1['alpha_0.5']['roles'][r]['aciertos']} · {c1['roles'][r]['aciertos']} |")
    m1, mv1, mv2 = (_acc_eo(v1["alpha_1.0"]["roles"]), _acc_eo(v1["alpha_0.5"]["roles"]),
                    _acc_eo(c1["roles"]))
    L += ["", "**Matcher por grupo** (α = 1 · v1 con α = 0,5 · v2 con α = 0,5):", "",
          "| Métrica | α = 1 | v1 | v2 |", "|---|---|---|---|"]
    for nombre, f in (("aciertos AR", lambda x: x["aciertos_por_grupo"]["tasas"]["AR"]),
                      ("aciertos no-AR", lambda x: x["aciertos_por_grupo"]["tasas"]["no-AR"]),
                      ("paridad demográfica", lambda x: x["paridad_demografica"]),
                      ("odds igualadas (EO)", lambda x: x["eo"]["eo"]),
                      ("ΔTPR", lambda x: x["eo"]["delta_tpr"]),
                      ("ΔFPR", lambda x: x["eo"]["delta_fpr"])):
        L.append(f"| {nombre} | {num(f(m1), 3)} | {num(f(mv1), 3)} | {num(f(mv2), 3)} |")
    L += ["", f"## Condición con sesgo programado («{ROTULO_PROG}»), α = 0,5", "",
          "| Magnitud | Ajuste v2 aplicado · no aplicable (de las planificaciones con candidatas) | "
          "Cambios de acción frente a α = 1 (v1 · v2) | Paridad demográfica (α = 1 · v1 · v2) | "
          "EO (α = 1 · v1 · v2) | Aciertos AR / no-AR (α = 1 · v2) | Deriva (ii) (v2) |",
          "|---|---|---|---|---|---|---|"]
    for mag, x in res["corrida_2"].items():
        c_a1 = s1[mag]["configuraciones"]["alpha_1"]
        c_v1 = s1[mag]["configuraciones"]["alpha_0_5"]
        aj = x["ajuste_v2"]
        L.append(f"| {mag.replace('_', ' ')} | {aj['aplicado']} · "
                 f"{aj['no_aplicable_falta_evidencia']} (de {aj['con_candidatas']}) | "
                 f"{c_v1['alpha_0_5']['accion_cambiada']} · {x['alpha_0_5']['accion_cambiada']} | "
                 f"{num(c_a1['brecha_toda_la_corrida'], 3)} · "
                 f"{num(c_v1['brecha_toda_la_corrida'], 3)} · "
                 f"{num(x['brecha_toda_la_corrida'], 3)} | "
                 f"{num(c_a1['odds_igualadas']['eo'], 3)} · {num(c_v1['odds_igualadas']['eo'], 3)} "
                 f"· {num(x['odds_igualadas']['eo'], 3)} | "
                 f"{num(c_a1['aciertos_por_grupo']['tasas']['AR'], 3)} / "
                 f"{num(c_a1['aciertos_por_grupo']['tasas']['no-AR'], 3)} · "
                 f"{num(x['aciertos_por_grupo']['tasas']['AR'], 3)} / "
                 f"{num(x['aciertos_por_grupo']['tasas']['no-AR'], 3)} | "
                 f"{len(x['ventanas_derivadas_regla_acumulada'])} |")
    L += ["", "**Advertencia.** Dentro de una celda con la acción fija, ê(Si, A) mide si esa acción "
          "se equivoca más con un grupo que con el otro, lo que pasa cuando la Si no captura algo "
          "relacionado con el grupo. No mide trato desigual: ese se ve en la ventana.", ""]
    (destino / "p5_equidad_v2.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def correr(out=None) -> dict:
    cfg = cargar_config()
    destino = out_dir(out)
    res = {"corrida_1": corrida_1_v2(cfg), "corrida_2": corrida_2_v2(cfg)}
    guardar_json({"demo": "E6 v2 · equidad por celda (Si, A), solo α = 0,5",
                  "rotulo_programado": ROTULO_PROG, **res}, "p5_equidad_v2.json", destino)
    escribir_md(res, destino)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None)
    r = correr(ap.parse_args().out)
    for ro in ROLES_PLAN:
        x = r["corrida_1"]["roles"][ro]
        print(ro, x["ajuste_v2"], x["alpha_0_5"]["eleccion_cambiada"],
              x["alpha_0_5"]["accion_cambiada"], x["aciertos"])
    for mag, x in r["corrida_2"].items():
        print(mag, x["ajuste_v2"], x["alpha_0_5"]["accion_cambiada"], x["brecha_toda_la_corrida"],
              x["odds_igualadas"]["eo"], x["estado_final"])
