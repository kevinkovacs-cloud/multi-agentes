#!/usr/bin/env python
"""
Control post hoc de la condición con sesgo programado (E6_RESPUESTA, decisión 4). Rótulo:
«control agregado después de ver los resultados; no pre-registrado».

Un Matcher que aprende sobre los mismos casos de la corrida 2 de E6, sin el rasgo
`titulo_local` en la Si y con el operador BIO sin sesgo (el de P1), con α = 1. Separa la tasa
base del sesgo residual que deja el operador sesgado. Descriptivo: no cambia ninguna regla ni
conclusión pre-registrada.

Salida: docs/parada_tecnica/p5_control_post_hoc.json.

Uso:  python experiments/parada_tecnica/p5_control_post_hoc.py [--out DIR]
"""
from __future__ import annotations
import argparse
import json

from comun_pt import OUT_DEFAULT, cargar_config, guardar_json, out_dir
from p5_metricas_equidad import calificados_del_flujo, correr_matcher, flujo_sesgo, metricas_sesgo
from moav_hr.instances.hr.roles_llc import RolMatcherLLC


def correr(out=None) -> dict:
    cfg = cargar_config()
    destino = out_dir(out)
    sp = cfg["equipo_e6"]["sesgo_programado"]
    rotulo = cfg["equipo_e6_v2"]["control_post_hoc"]["rotulo"]
    s1 = json.loads((OUT_DEFAULT / "p5_sesgo_programado.json").read_text(encoding="utf-8"))
    # los casos y la verdad son los mismos en las dos magnitudes; el rasgo no se usa
    casos = flujo_sesgo(cfg, sp["magnitudes"]["detectable"])
    rol = RolMatcherLLC(cfg["entorno"]["ruido_wio_epsilon"], sp["semilla_casos"])
    motor = correr_matcher(cfg, casos, "Matcher-control-sin-sesgo", "alpha_1", rol=rol)
    x = metricas_sesgo(cfg, motor, casos)
    control = {k: x[k] for k in ("estado_final", "brecha_toda_la_corrida", "brecha_por_tercio",
                                 "odds_igualadas", "aciertos_por_grupo", "evolucion",
                                 "ventanas_derivadas_regla_ventana",
                                 "ventanas_derivadas_regla_acumulada")}
    motivos: dict = {}
    for reg in motor.ciclos:
        motivos.setdefault(reg["capa"], {}).setdefault(reg["motivo"], 0)
        motivos[reg["capa"]][reg["motivo"]] += 1
    control["motivos_por_capa"] = motivos

    def operador(pv):
        return round(sum(v["actua_el_operador"] for v in pv) / len(pv), 4)
    control["fraccion_operador_bio"] = operador(x["por_ventana"])
    frente = {}
    for mag in sp["magnitudes"]:
        sesgado = s1[mag]["configuraciones"]["alpha_1"]
        frente[mag] = {
            "paridad_demografica": {"sesgado": sesgado["brecha_toda_la_corrida"],
                                    "control": control["brecha_toda_la_corrida"],
                                    "diferencia": round(sesgado["brecha_toda_la_corrida"]
                                                        - control["brecha_toda_la_corrida"], 4)},
            "odds_igualadas": {"sesgado": sesgado["odds_igualadas"]["eo"],
                               "control": control["odds_igualadas"]["eo"],
                               "diferencia": round(sesgado["odds_igualadas"]["eo"]
                                                   - control["odds_igualadas"]["eo"], 4)},
            "aciertos_por_grupo": {"sesgado": sesgado["aciertos_por_grupo"]["tasas"],
                                   "control": control["aciertos_por_grupo"]["tasas"]},
            "estado_final": {"sesgado": sesgado["estado_final"],
                             "control": control["estado_final"]},
            "fraccion_operador_bio": {"sesgado": operador(sesgado["por_ventana"]),
                                      "control": control["fraccion_operador_bio"]}}
    res = {"rotulo": rotulo, "calificados_del_flujo": calificados_del_flujo(cfg),
           "control": control, "frente_al_matcher_sesgado_que_aprende": frente}
    guardar_json({"demo": "E6 · control post hoc sin sesgo programado", **res},
                 "p5_control_post_hoc.json", destino)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None)
    r = correr(ap.parse_args().out)
    print(json.dumps({"control": {k: r["control"][k] for k in ("estado_final",
                                                                "brecha_toda_la_corrida")},
                      "frente": r["frente_al_matcher_sesgado_que_aprende"]},
                     ensure_ascii=False, indent=1))
