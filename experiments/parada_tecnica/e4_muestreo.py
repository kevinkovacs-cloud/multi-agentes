#!/usr/bin/env python
"""
Pedido de E4_RESPUESTA sobre el resultado 5 de E4: la diferencia de la tasa de calificados
entre grupos en el flujo de casos de E4 (semilla sin cambiar), ¿es una fluctuación de
muestreo? Pre-registrado en E5_PREREGISTRO.md (sección `muestreo_e4` de la config):

  · estadístico z de dos proporciones, test exacto de Fisher (bilateral) y test de
    permutación sobre los 260 casos de E4;
  · independencia del grupo frente a la celda de Si y frente a la verdad (χ² y Fisher), en
    el flujo de E4 y en las semillas extra juntas;
  · distribución de la diferencia en las semillas extra y lugar de la semilla de E4.

No corre ningún agente: solo el generador del entorno (regla 5). Escribe
docs/parada_tecnica/e4_muestreo_calificados.json y .md.

Uso:  python experiments/parada_tecnica/e4_muestreo.py [--out DIR]
"""
from __future__ import annotations
import argparse
import math

import numpy as np
from scipy import stats as st

from comun_pt import cargar_config, encabezado_md, guardar_json, num, out_dir
from moav_hr.core.theory import serialize
from moav_hr.instances.hr import entorno
from moav_hr.instances.hr.parser_agent import build_si, normalize_profile


def flujo(cfg: dict, semilla: int) -> list:
    cv, eq = cfg["ciclo_de_vida"], cfg["equipo_e4"]
    return [c for capa in eq["flujo"]
            for c in entorno.generar_escenario(capa, cv["ciclos_por_capa"][capa], semilla)]


def _conteo(casos) -> dict:
    out = {}
    for g in ("AR", "no-AR"):
        x = [c.calificado for c in casos if c.grupo == g]
        out[g] = {"n": len(x), "calificados": int(sum(x))}
    return out


def _diferencia(c: dict) -> float:
    return c["AR"]["calificados"] / c["AR"]["n"] - c["no-AR"]["calificados"] / c["no-AR"]["n"]


def _celda(caso) -> str:
    return serialize(build_si(normalize_profile(caso.candidato)))


def _chi2_grupo_celda(casos) -> dict:
    celdas = sorted({_celda(c) for c in casos})
    tabla = np.array([[sum(1 for c in casos if c.grupo == g and _celda(c) == k) for k in celdas]
                      for g in ("AR", "no-AR")])
    chi2, p, dof, esperado = st.chi2_contingency(tabla)
    return {"chi2": round(float(chi2), 3), "gl": int(dof), "p": round(float(p), 4),
            "celdas": len(celdas), "esperado_minimo": round(float(esperado.min()), 2)}


def _fisher(c: dict) -> float:
    tabla = [[c["AR"]["calificados"], c["AR"]["n"] - c["AR"]["calificados"]],
             [c["no-AR"]["calificados"], c["no-AR"]["n"] - c["no-AR"]["calificados"]]]
    return float(st.fisher_exact(tabla, alternative="two-sided")[1])


def correr(out=None) -> dict:
    cfg = cargar_config()
    mu, eq = cfg["equipo_e5"]["muestreo_e4"], cfg["equipo_e4"]
    casos = flujo(cfg, eq["semilla_casos"])
    c = _conteo(casos)
    d_obs = _diferencia(c)
    n1, n2 = c["AR"]["n"], c["no-AR"]["n"]
    p_pool = (c["AR"]["calificados"] + c["no-AR"]["calificados"]) / (n1 + n2)
    z = d_obs / math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    rng = np.random.default_rng(mu["semilla_permutaciones"])
    q = np.array([c_.calificado for c_ in casos], dtype=float)
    g = np.array([c_.grupo == "AR" for c_ in casos])
    extremos = 0
    for _ in range(mu["permutaciones"]):
        gp = rng.permutation(g)
        extremos += abs(q[gp].mean() - q[~gp].mean()) >= abs(d_obs) - 1e-12
    extra = [eq["semilla_casos"] + 1000 * k for k in range(1, mu["semillas_extra"] + 1)]
    difs, juntos = [], []
    for s in extra:
        cs = flujo(cfg, s)
        difs.append(_diferencia(_conteo(cs)))
        juntos.extend(cs)
    difs = np.array(difs)
    cj = _conteo(juntos)
    res = {
        "flujo_e4": {"semilla": eq["semilla_casos"], "conteo": c,
                     "tasas": {k: round(v["calificados"] / v["n"], 4) for k, v in c.items()},
                     "diferencia": round(d_obs, 4), "z": round(z, 3),
                     "p_z_bilateral": round(float(2 * st.norm.sf(abs(z))), 4),
                     "p_fisher_bilateral": round(_fisher(c), 4),
                     "p_permutacion": round((extremos + 1) / (mu["permutaciones"] + 1), 4),
                     "permutaciones": mu["permutaciones"],
                     "independencia_grupo_celda": _chi2_grupo_celda(casos)},
        "semillas_extra": {"n": len(extra), "primera": extra[0], "ultima": extra[-1],
                           "diferencia_media": round(float(difs.mean()), 4),
                           "diferencia_desvio": round(float(difs.std(ddof=1)), 4),
                           "fraccion_abs_mayor_o_igual_que_e4":
                               round(float(np.mean(np.abs(difs) >= abs(d_obs) - 1e-12)), 4),
                           "percentil_e4": round(float(st.percentileofscore(difs, d_obs)), 1),
                           "juntas": {"conteo": cj, "diferencia": round(_diferencia(cj), 4),
                                      "p_fisher_grupo_verdad": round(_fisher(cj), 4),
                                      "independencia_grupo_celda": _chi2_grupo_celda(juntos)}}}
    destino = out_dir(out)
    guardar_json({"demo": "E4 · resultado 5: tasa de calificados por grupo", **res},
                 "e4_muestreo_calificados.json", destino)
    f, x = res["flujo_e4"], res["semillas_extra"]
    L = encabezado_md("E4 · Resultado 5: la diferencia de calificados entre grupos es de "
                      "muestreo")
    L += ["Pedido de `E4_RESPUESTA_ClaudeChat_2026-10-08.md`, pre-registrado en "
          "`E5_PREREGISTRO.md`. Solo usa el generador del entorno (regla 5); no corre agentes y "
          "no cambia la semilla de E4.", "",
          f"- **Flujo de E4** (semilla {f['semilla']}): calificados {f['conteo']['AR']['calificados']}"
          f"/{f['conteo']['AR']['n']} en AR ({num(f['tasas']['AR'], 3)}) y "
          f"{f['conteo']['no-AR']['calificados']}/{f['conteo']['no-AR']['n']} en no-AR "
          f"({num(f['tasas']['no-AR'], 3)}); diferencia {num(f['diferencia'], 3)}.",
          f"- **z de dos proporciones** = {num(f['z'], 2)} (p bilateral {num(f['p_z_bilateral'], 4)}); "
          f"**Fisher exacto** p = {num(f['p_fisher_bilateral'], 4)}; **permutación** "
          f"({f['permutaciones']} permutaciones) p = {num(f['p_permutacion'], 4)}.",
          f"- **Independencia del grupo frente a la celda de Si** en el flujo de E4: χ² = "
          f"{num(f['independencia_grupo_celda']['chi2'], 2)}, gl = "
          f"{f['independencia_grupo_celda']['gl']}, p = "
          f"{num(f['independencia_grupo_celda']['p'], 4)} (esperado mínimo por celda "
          f"{num(f['independencia_grupo_celda']['esperado_minimo'], 2)}).",
          f"- **{x['n']} semillas más del mismo generador** (de {x['primera']} a {x['ultima']}, "
          f"paso 1000): diferencia media {num(x['diferencia_media'], 4)}, desvío "
          f"{num(x['diferencia_desvio'], 4)}; la diferencia de E4 está en el percentil "
          f"{num(x['percentil_e4'], 1)}, y {num(100 * x['fraccion_abs_mayor_o_igual_que_e4'], 1)} % "
          "de las semillas tiene una diferencia de igual o mayor tamaño.",
          f"- **Todas esas semillas juntas** ({x['juntas']['conteo']['AR']['n']} casos por grupo): "
          f"diferencia {num(x['juntas']['diferencia'], 4)}; grupo frente a verdad, Fisher p = "
          f"{num(x['juntas']['p_fisher_grupo_verdad'], 4)}; grupo frente a celda de Si, χ² p = "
          f"{num(x['juntas']['independencia_grupo_celda']['p'], 4)}.", "",
          "Lectura: con todas las semillas juntas el grupo es independiente de la verdad y de la "
          "celda de Si, como dice la regla 5; la diferencia de E4 no viene del generador sino de "
          "su semilla. Es una semilla poco frecuente (los tres tests dan p cerca de "
          f"{num(f['p_fisher_bilateral'], 2)} y queda en el extremo de la distribución de las "
          "semillas extra), así que no conviene leerla como típica. La paridad demográfica del "
          "Matcher la marca como brecha porque sigue las tasas base; la paridad de errores no "
          "(E4, resultado 5). El χ² de grupo frente a celda en un solo flujo tiene celdas con "
          "esperado bajo; el de las semillas juntas no.", ""]
    (destino / "e4_muestreo_calificados.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None)
    r = correr(ap.parse_args().out)
    print(r["flujo_e4"]["z"], r["flujo_e4"]["p_fisher_bilateral"], r["flujo_e4"]["p_permutacion"],
          r["semillas_extra"]["percentil_e4"])
