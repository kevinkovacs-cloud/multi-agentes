#!/usr/bin/env python
"""
Pre-registro del entorno del Bloque E: escribe docs/parada_tecnica/E2_PREREGISTRO_ENTORNO.md
a partir de las reglas de `instances/hr/entorno.py` y de `configs/parada_tecnica.yaml`.
No corre ningún agente: todas las cifras son valores esperados de las reglas.

Uso:  python experiments/parada_tecnica/preregistro.py [--out DIR]
"""
from __future__ import annotations
import argparse

from comun_pt import cargar_config, encabezado_md, num, out_dir
from moav_hr.instances.hr import entorno


def escribir(out=None) -> str:
    cfg = cargar_config()
    eps = cfg["entorno"]["ruido_wio_epsilon"]
    d = entorno.describir_entorno(eps)
    cv = cfg["ciclo_de_vida"]
    L = encabezado_md("E2 · Pre-registro del entorno simulado (Bloque E)")
    L += ["Reglas fijadas **antes** de la primera corrida de P1 (decisión P1 de Claude chat). "
          "Fuente de las reglas: `src/moav_hr/instances/hr/entorno.py`; parámetros: "
          "`configs/parada_tecnica.yaml`.", "",
          "## Reglas", "",
          "- **Verdad latente** (igual para todos los grupos): calificado con probabilidad "
          f"{num(entorno.Q_REQUISITOS, 1)} si la Si cumple los requisitos del puesto (antigüedad "
          f"mínima y al menos 1 skill clave), {num(entorno.Q_SIN_REQUISITOS, 1)} si no.",
          "- **Operador BIO del Matcher:** ADVANCE si la Si tiene al menos 2 skills clave.",
          "- **Respuesta en la región 3:** BIO y TBO, etiqueta del escenario; WIO, revisión "
          f"humana simulada (`human_sim` noisy, ε = {num(eps, 2)}).",
          "- **Grupo** (plano de auditoría): alternado por índice de caso, independiente de la Si "
          "y de la verdad.",
          f"- **Ciclos por capa:** BIO {cv['ciclos_por_capa']['BIO']}, TBO "
          f"{cv['ciclos_por_capa']['TBO']}, WIO {cv['ciclos_por_capa']['WIO']}; intervalo "
          f"n = {cv['n_intervalo']}; %RCE = {cv['rce']}, %RTN = {cv['rtn']}.", "",
          "## Valores esperados por capa (de las reglas, sin correr agentes)", "",
          "| Capa | Celdas | Precisión esperada del operador BIO | Precisión esperada de la mejor "
          "acción por celda | Mejora máxima posible sobre el neutro |",
          "|---|---|---|---|---|"]
    for capa in entorno.CAPAS:
        c = d[capa]
        mejora = 100 * (c["precision_esperada_mejor"] - c["precision_esperada_bio"]) \
            / c["precision_esperada_bio"]
        L.append(f"| {capa} | {c['n_celdas']} | {num(c['precision_esperada_bio'], 3)} | "
                 f"{num(c['precision_esperada_mejor'], 3)} | {num(mejora, 1)} % |")
    L += ["", "La «mejora máxima posible» supone que el agente aprende la mejor acción en "
          "todas las celdas. En WIO el planificador no explora (DE-3): en las celdas que no vio "
          "en TBO (educación Doctorado) actúa con el operador BIO, así que su mejora esperada "
          "queda por debajo de esa cota. Las precisiones de WIO se miden contra la revisión "
          "humana con ruido, que es lo que observa el agente.", ""]
    for capa in entorno.CAPAS:
        L += [f"## Celdas de la capa {capa}", "",
              "| Si (skills · banda · educación) | Frecuencia | P(calificado) | Acción BIO | "
              "Precisión BIO | Mejor acción | Precisión mejor |", "|---|---|---|---|---|---|---|"]
        for f in d[capa]["celdas"]:
            si = f["si"]
            L.append(f"| {si['skills_match']} · {si['exp_band']} · {si['edu']} | "
                     f"{num(f['frecuencia'], 3)} | {num(f['prob_calificado'], 2)} | "
                     f"{f['accion_bio']} | {num(f['precision_bio'], 3)} | {f['mejor_accion']} | "
                     f"{num(f['precision_mejor'], 3)} |")
        L.append("")
    texto = "\n".join(L)
    (out_dir(out) / "E2_PREREGISTRO_ENTORNO.md").write_text(texto, encoding="utf-8")
    return texto


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Pre-registro del entorno (Bloque E)")
    ap.add_argument("--out", default=None)
    escribir(ap.parse_args().out)
    print("E2_PREREGISTRO_ENTORNO.md escrito")
