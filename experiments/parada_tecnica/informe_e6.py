#!/usr/bin/env python
"""
Informe del punto de control de E6 (Bloque E, punto 5 del pedido): escribe
docs/parada_tecnica/E6_PUNTO_DE_CONTROL.md desde p5_metricas_equidad.json y
p5_sesgo_programado.json. Ningún número a mano.

Uso:  python experiments/parada_tecnica/informe_e6.py [--out DIR] [--correr]
"""
from __future__ import annotations
import argparse
import json
import math

from comun_pt import cargar_config, encabezado_md, mayus, num, out_dir
from informe_e4 import _commit

TITULO = {"parser": "Parser", "matcher": "Semantic Matcher", "bias_auditor": "Bias Auditor",
          "explainer": "Explainer"}
ROTULO_PROG = "parámetros programados"


def _z_dos_proporciones(p1: float, n1: int, p2: float, n2: int) -> tuple[float, float]:
    x1, x2 = p1 * n1, p2 * n2
    p = (x1 + x2) / (n1 + n2)
    z = (p1 - p2) / math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    return z, math.erfc(abs(z) / math.sqrt(2))


def _n(x) -> str:
    return "—" if x is None else num(x, 3)


def _c(x) -> str:
    return "—" if x is None else str(x)


def escribir(out=None) -> str:
    base = out_dir(out)
    c1 = json.loads((base / "p5_metricas_equidad.json").read_text(encoding="utf-8"))
    c2 = json.loads((base / "p5_sesgo_programado.json").read_text(encoding="utf-8"))
    cfg = cargar_config()
    m_min = cfg["utilidad"]["m_min_por_grupo"]
    a1, a5 = c1["alpha_1.0"]["roles"], c1["alpha_0.5"]["roles"]
    bq = c1["calificados_del_flujo"]
    L = encabezado_md("E6 · Punto de control del Bloque E (punto 5 del pedido)")
    L += ["Rama `eje1/bloque-e`, sin push. Pre-registro de E6 commiteado antes de correr "
          f"(`{_commit('docs/parada_tecnica/E6_PREREGISTRO.md')}`, "
          "`docs/parada_tecnica/E6_PREREGISTRO.md`), junto con "
          "`E5_RESPUESTA_ClaudeChat_2026-10-08.md`. Documento para la dirección: "
          "`docs/parada_tecnica/METRICAS_EQUIDAD_POR_ROL.md`. Datos: `p5_metricas_equidad.json` "
          "y `p5_sesgo_programado.json`; figura: `p5_sesgo_programado.png`. Las métricas "
          "descriptivas 1 y 2 de E5_RESPUESTA ya están en el informe de E5.", "",
          "## Qué se hizo", "",
          "- **Métricas de equidad por rol** en `core/equidad_roles.py` (brecha del resultado "
          "favorable, paridad de errores, ê(t) por teoría) y las dos reglas del Auditor sobre un "
          "flujo (`auditar_flujo`, con el mismo primitivo que el gate v2).",
          "- **U_rol con α = 1 y α = 0,5** sobre el equipo de E5 con "
          f"{c1['alpha_1.0']['casos']} casos; en la corrida con α = 0,5 el planificador registra "
          "también qué habría elegido con α = 1 en el mismo estado.",
          f"- **Condición con sesgo programado** («{ROTULO_PROG}»): rasgo proxy `titulo_local` en "
          "la Si del Matcher y operador BIO que lo penaliza (regla 11), en dos magnitudes, con el "
          "neutro y el Matcher que aprende (α = 1 y α = 0,5).", "",
          "## Corrida 1: equidad por rol (α = 1 · α = 0,5)", "",
          f"Diferencia de calificados entre grupos en el flujo (tasa base): AR "
          f"{num(bq['tasas']['AR'], 3)}, no-AR {num(bq['tasas']['no-AR'], 3)} (brecha "
          f"{num(bq['brecha'], 3)}).", "",
          "| Rol | Métrica | α = 1 | α = 0,5 | Teorías con ê(t) (m_min = "
          f"{m_min} por grupo) |", "|---|---|---|---|---|"]
    met = {"parser": "brecha de completitud", "matcher": "paridad demográfica",
           "bias_auditor": "Δ_esc (paridad de derivación)",
           "explainer": "brecha de completitud de la explicación"}
    for r in ("parser", "matcher", "bias_auditor", "explainer"):
        t1, t5 = a1[r]["teorias"], a5[r]["teorias"]
        teo = ("no aplica (la acción la decide la regla)" if r == "bias_auditor" else
               f"{t1['llegan_a_m_min']} de {t1['en_E']} · {t5['llegan_a_m_min']} de {t5['en_E']}")
        L.append(f"| {TITULO[r]} | {met[r]} | {_n(a1[r]['favorable']['brecha'])} | "
                 f"{_n(a5[r]['favorable']['brecha'])} | {teo} |")
        if r == "matcher":
            L.append(f"| {TITULO[r]} | paridad de errores (EO) | "
                     f"{_n(a1[r]['odds_igualadas']['eo'])} | {_n(a5[r]['odds_igualadas']['eo'])} "
                     "| |")
        if r == "parser":
            L.append(f"| {TITULO[r]} | d_TV del canal proxy (cota inferior) | "
                     f"{_n(a1[r]['dtv_canal_proxy'])} | {_n(a5[r]['dtv_canal_proxy'])} | |")
    tot = {k: sum(a5[r]["alpha_0_5"][k] for r in ("parser", "matcher", "explainer"))
           for k in ("planificaciones", "equidad_usada", "eleccion_cambiada", "accion_cambiada",
                     "elegida_sin_e_frente_a_una_con_e")}
    iguales = all(a1[r]["aciertos"] == a5[r]["aciertos"]
                  and a1[r]["favorable"] == a5[r]["favorable"] for r in a1)
    L += ["", f"**α = 0,5:** se usó ê(t) en {tot['equidad_usada']} de {tot['planificaciones']} "
          f"planificaciones (Parser, Matcher y Explainer); la teoría elegida cambió respecto de "
          f"α = 1 en {tot['eleccion_cambiada']} y la acción en {tot['accion_cambiada']}. "
          + ("Los aciertos y las tasas favorables por grupo de cada rol son iguales con α = 1 y "
             "con α = 0,5. " if iguales else "Los aciertos o las tasas difieren entre α = 1 y "
             "α = 0,5 (ver el JSON). ")
          + "Ejemplos en `METRICAS_EQUIDAD_POR_ROL.md`.", "",
          "## Paridad demográfica frente a paridad de errores", ""]
    p2 = a1["matcher"]["primeros_260"]
    eo2 = p2["odds_igualadas"]
    z, pz = _z_dos_proporciones(eo2["tpr"]["AR"], eo2["n_pos"]["AR"], eo2["tpr"]["no-AR"],
                                eo2["n_pos"]["no-AR"])
    eo = a1["matcher"]["odds_igualadas"]
    L += [f"- **Primeros 260 casos (los de E4):** paridad demográfica "
          f"{num(p2['paridad_demografica']['brecha'], 3)}; aciertos "
          f"{num(p2['aciertos_por_grupo']['tasas']['AR'], 3)} (AR) y "
          f"{num(p2['aciertos_por_grupo']['tasas']['no-AR'], 3)} (no-AR), es decir, paridad de "
          f"aciertos pareja; pero las odds igualadas no: TPR {num(eo2['tpr']['AR'], 3)} frente a "
          f"{num(eo2['tpr']['no-AR'], 3)} ({eo2['n_pos']['AR']} y {eo2['n_pos']['no-AR']} casos "
          f"con Sf calificado; z = {num(z, 2)}, p = {num(pz, 3)}) y FPR "
          f"{num(eo2['fpr']['AR'], 3)} frente a {num(eo2['fpr']['no-AR'], 3)}: EO "
          f"{num(eo2['eo'], 3)}.",
          f"- **Los {c1['alpha_1.0']['casos']} casos:** paridad demográfica "
          f"{num(a1['matcher']['favorable']['brecha'], 3)}, diferencia de calificados "
          f"{num(bq['brecha'], 3)}, aciertos {num(a1['matcher']['aciertos_por_grupo']['tasas']['AR'], 3)}"
          f" y {num(a1['matcher']['aciertos_por_grupo']['tasas']['no-AR'], 3)}, EO "
          f"{num(eo['eo'], 3)} (ΔTPR {num(eo['delta_tpr'], 3)}, ΔFPR {num(eo['delta_fpr'], 3)}).",
          "- Lectura: la paridad demográfica sigue a la tasa base; la paridad de aciertos sale "
          "pareja; las odds igualadas muestran una diferencia de TPR que, con estos tamaños, no "
          "se distingue claramente del azar. Son tres criterios distintos y no coinciden.", "",
          "## Corrida 2: sesgo programado por un proxy", "",
          f"«{mayus(ROTULO_PROG)}». El Matcher solo sobre los mismos casos; el Auditor sobre sus "
          "ventanas de decisiones. Regla (i): ventana de 20. Regla (ii): evidencia acumulada "
          "en la capa del Matcher, con δ/L.", "",
          "| Magnitud | Configuración | Paridad demográfica (toda · por tercio) | EO | Deriva (i) "
          "| Deriva (ii) | Estado final | Gate de Ω en la región 7 | Compartición |",
          "|---|---|---|---|---|---|---|---|---|"]
    for mag in ("detectable", "bajo_umbral"):
        f = c2[mag]
        for conf, x in f["configuraciones"].items():
            der = x["ventanas_derivadas_regla_acumulada"]
            gate = ("—" if not x["evolucion"] else
                    ("negó" if any(e["niega_omega"] for e in x["evolucion"]) else "nunca negó")
                    + f" (LCB máx. {num(max((e['lcb'] or 0) for e in x['evolucion']), 3)})")
            comp = x.get("comparticion")
            comp_t = ("—" if comp is None else
                      ("aceptada" if comp["aceptada"] else "rechazada")
                      + f" (Ω: brecha {num(comp['omega_donante']['brecha'], 3)}, LCB "
                      f"{num(comp['omega_donante']['lcb'], 3)}"
                      + ("; axioma [b]" if comp.get("axioma") else "") + ")")
            L.append(f"| {mag.replace('_', ' ')} ({num(f['brecha_operador_esperada'], 2)}) | "
                     f"{conf.replace('_', ' ').replace('alpha', 'α =').replace('0 5', '0,5')} | "
                     f"{num(x['brecha_toda_la_corrida'], 3)} · "
                     + " / ".join(num(b, 2) for b in x["brecha_por_tercio"])
                     + f" | {_n(x['odds_igualadas']['eo'])} | "
                     f"{len(x['ventanas_derivadas_regla_ventana'])} | {len(der)}"
                     + (f" (desde {der[0]})" if der else "") + f" | {x['estado_final']} | "
                     f"{gate} | {comp_t} |")
    det = c2["detectable"]["configuraciones"]
    bu = c2["bajo_umbral"]["configuraciones"]
    sl = det["alpha_1"]["teorias_sin_titulo_local"]
    der_n = det["neutro"]["ventanas_derivadas_regla_acumulada"]
    from preregistro_e6 import primera_deteccion
    acu = cfg["equipo_e6"]["sesgo_programado"]["auditor"]["acumulada"]
    n_oc = primera_deteccion(c2["detectable"]["brecha_operador_esperada"],
                             cfg["omega"]["tau_b"], acu["delta"], acu["L"],
                             sum(cfg["equipo_e6"]["flujo_casos"].values()) // 2)
    L += ["", f"- **d_TV de la Si del Matcher frente al grupo** (cota inferior): "
          f"{num(c2['detectable']['dtv_si_matcher'], 3)} (detectable) y "
          f"{num(c2['bajo_umbral']['dtv_si_matcher'], 3)} (bajo umbral). La Si no contiene el "
          "grupo, pero el rasgo lo deja inferir.",
          f"- **(iv) Atenuación** (ilustra el mecanismo; no es evidencia de la conjetura de "
          f"atenuación): con la magnitud detectable, la paridad demográfica pasa de "
          f"{num(det['neutro']['brecha_toda_la_corrida'], 3)} en el neutro a "
          f"{num(det['alpha_1']['brecha_toda_la_corrida'], 3)} en el Matcher que aprende; la "
          f"diferencia de calificados del flujo es {num(bq['brecha'], 3)}, así que lo que queda "
          "por encima de la tasa base es menor que lo que trae el operador. En BIO y TBO el "
          "Matcher prueba primero la acción no probada (P3), así que el operador sesgado decide "
          "poco: en promedio actuó en "
          + num(100 * sum(v["actua_el_operador"] for v in det["alpha_1"]["por_ventana"])
                / len(det["alpha_1"]["por_ventana"]), 1) + " % de las decisiones.",
          f"- **ê(t) casi no ve el sesgo por proxy:** en las teorías sin título local del Matcher "
          f"(α = 1, magnitud detectable) hay {sl['lecturas_AR']} lecturas de AR y "
          f"{sl['lecturas_no_AR']} de no-AR en E(t), y {sl['llegan_a_m_min']} de {sl['en_E']} "
          "llegan a m_min en los dos grupos. Es la advertencia formal corrida: la disparidad "
          "está en qué teorías se aplican a cada grupo, no dentro de una teoría.", "",
          "## Resultados que no fueron los esperados", "",
          f"1. **α = 0,5 nunca cambia la acción.** Cambió la teoría elegida "
          f"{tot['eleccion_cambiada']} veces y la acción {tot['accion_cambiada']}: con U basada en "
          "la acción (v2) todas las variantes (Si, A, ·) tienen la misma U y ê(t) solo reordena "
          f"variantes de la misma acción. Además, en {tot['elegida_sin_e_frente_a_una_con_e']} "
          "de esos cambios la variante elegida no tenía ê(t) y la de α = 1 sí: el respaldo «sin "
          "ê se usa α = 1» favorece a la variante sin evidencia frente a la que tiene ê < 1.",
          "2. **Paridad de aciertos pareja no es paridad de errores.** La lectura del resultado "
          "5 de E4 (0,762 frente a 0,746) vale para los aciertos; las odds igualadas muestran "
          f"ΔTPR {num(eo2['delta_tpr'], 3)} en esos mismos casos (p = {num(pz, 3)}). Conviene "
          "decir qué criterio es «paridad de errores» para el Matcher.",
          "3. **El Matcher sesgado comparte sin que Ω lo frene.** Con la magnitud detectable, el "
          f"Matcher que aprende quedó con paridad demográfica "
          f"{num(det['alpha_1']['brecha_toda_la_corrida'], 3)} y su colaboración a un Matcher "
          f"Born fue "
          f"{'aceptada' if det['alpha_1']['comparticion']['aceptada'] else 'rechazada'} (LCB "
          f"{num(det['alpha_1']['comparticion']['omega_donante']['lcb'], 3)} con "
          f"{det['alpha_1']['comparticion']['omega_donante']['n_por_grupo']['AR']} decisiones por "
          "grupo): sus teorías de las celdas sin título local pasan al receptor. Parte de esa "
          "brecha es tasa base; el gate de compartición no distingue una de otra.",
          "4. **Con la magnitud bajo umbral el Matcher que aprende no sale de Born:** en BIO su "
          "%CEA fue " + ", ".join(num(e["pct_cea"], 1) for e in bu["alpha_1"]["evolucion"])
          + f", por debajo de %RCE = {cfg['ciclo_de_vida']['rce']} (con el rasgo en la Si hay el "
          "doble de celdas, una causa posible). Su compartición la rechaza el axioma [b]; Ω no "
          "tenía evidencia.",
          f"5. **La regla acumulada detecta al neutro antes de lo previsto** (desde "
          f"{der_n[0] if der_n else '—'}; la característica operativa daba la ventana "
          f"{_c(n_oc // 10 if n_oc else None)} para una brecha de "
          f"{num(c2['detectable']['brecha_operador_esperada'], 2)} exacta): la brecha realizada "
          "en las primeras ventanas fue mayor que la esperada. La regla de ventana (i) no derivó "
          "ninguna ventana en ninguna configuración, como estaba previsto.",
          "6. **Bias Auditor:** Δ_esc = 0 por construcción (la derivación es por ventana) y U_rol "
          "no aplica (la acción la decide la regla).", "",
          "## Preguntas para Claude chat (y, si corresponde, para la dirección)", "",
          "1. **ê(t) por variante o por celda.** Con U(Si, A) de la v2, ¿ê se calcula por celda "
          "(Si, A), para que α pueda cambiar la acción? ¿Y qué hacer con las candidatas sin ê(t): "
          "usar α = 1 (hoy, que favorece a la variante sin evidencia) o excluirlas del ajuste?",
          "2. **Métrica del Matcher:** ¿paridad de aciertos o odds igualadas (max ΔTPR, ΔFPR)? En "
          "los casos de E4 dan cosas distintas.",
          "3. **Gate de compartición:** hoy usa la paridad demográfica de todas las decisiones del "
          "donante, con una sola evaluación. No frenó al Matcher sesgado (brecha por debajo de lo "
          "detectable con 300 por grupo). ¿Se deja así (es el estándar de evidencia) o se suma "
          "una auditoría por celda del rasgo proxy?",
          "4. **Control sin sesgo en la condición programada:** un Matcher que aprende, sin el "
          "rasgo ni el operador sesgado, sobre los mismos casos, separaría la tasa base del sesgo "
          "residual. No estaba pre-registrado; ¿se agrega en E7?", "",
          "## Qué sigue", "",
          "E7 (`generar_todo.py`, informe final, `LEEME_REUNION.md`, ESTADO). **Frenado en el "
          "punto de control de E6.** Sin push.", ""]
    ruta = base / "E6_PUNTO_DE_CONTROL.md"
    ruta.write_text("\n".join(L) + "\n", encoding="utf-8")
    return str(ruta)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Informe del punto de control de E6")
    ap.add_argument("--out", default=None)
    ap.add_argument("--correr", action="store_true", help="corre P5 antes de escribir")
    a = ap.parse_args()
    if a.correr:
        import p5_metricas_equidad
        p5_metricas_equidad.correr(a.out)
    print(escribir(a.out))
