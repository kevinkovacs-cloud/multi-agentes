#!/usr/bin/env python
"""
Informe del punto de control de E5 (Bloque E, punto 3 del pedido): escribe
docs/parada_tecnica/E5_PUNTO_DE_CONTROL.md desde p3_equipos.json, e4_muestreo_calificados.json,
p4_equipo.json y las reglas pre-registradas. Ningún número a mano.

Uso:  python experiments/parada_tecnica/informe_e5.py [--out DIR] [--correr]
"""
from __future__ import annotations
import argparse
import json

from comun_pt import cargar_config, encabezado_md, num, out_dir
from informe_e4 import _commit
from moav_hr.instances.hr import entorno
from moav_hr.instances.hr.equipo_llc import seccion_equipo

TITULO = {"parser": "Parser", "matcher": "Semantic Matcher", "bias_auditor": "Bias Auditor",
          "explainer": "Explainer"}
ESTADOS = ("Novice", "Trained", "Mature")


def _ciclo(info: dict, a: str):
    return next((p["ciclo"] for p in info["promociones"] if p["a"] == a), None)


def _c(x) -> str:
    return "—" if x is None else str(x)


def defectos_por_grupo(cfg: dict, equipo: str, extra: int = 0) -> dict:
    """Documentos con defecto (regla 7) por grupo en el flujo del equipo y, con `extra` > 0,
    en ese número de semillas más (casos + 1000·k, documentos = casos + 1); sin agentes."""
    from scipy.stats import fisher_exact
    eq = seccion_equipo(cfg, "equipo_e5", cfg["equipo_e5"]["equipos"][equipo])
    cv = cfg["ciclo_de_vida"]

    def contar(semillas):
        out = {"AR": [0, 0], "no-AR": [0, 0]}
        for s_casos, s_docs in semillas:
            for capa in eq["flujo"]:
                for caso in entorno.generar_escenario(capa, cv["ciclos_por_capa"][capa],
                                                      s_casos):
                    _, defecto = entorno.plantilla_parser(caso, s_docs)
                    out[caso.grupo][0] += int(defecto)
                    out[caso.grupo][1] += 1
        p = fisher_exact([[out["AR"][0], out["AR"][1] - out["AR"][0]],
                          [out["no-AR"][0], out["no-AR"][1] - out["no-AR"][0]]])[1]
        return {**{g: {"defectos": d, "casos": n} for g, (d, n) in out.items()},
                "p_fisher": round(float(p), 4)}
    res = {"flujo": contar([(eq["semilla_casos"], eq["semilla_documentos"])])}
    if extra:
        res["extra"] = contar([(eq["semilla_casos"] + 1000 * k,
                                eq["semilla_casos"] + 1000 * k + 1) for k in range(1, extra + 1)])
    return res


def escribir(out=None) -> str:
    base = out_dir(out)
    d = json.loads((base / "p3_equipos.json").read_text(encoding="utf-8"))
    mu = json.loads((base / "e4_muestreo_calificados.json").read_text(encoding="utf-8"))
    p4 = json.loads((base / "p4_equipo.json").read_text(encoding="utf-8"))
    cfg = cargar_config()
    cv = cfg["ciclo_de_vida"]
    pre = entorno.describir_entorno_e4(cfg["omega"]["tau_b"], cfg["omega"]["delta"],
                                       cfg["equipo_e4"]["ventana"])
    m, roles = d["metricas"], d["config_e5"]["compartir_e5"]["roles"]
    L = encabezado_md("E5 · Punto de control del Bloque E (punto 3 del pedido)")
    L += ["Rama `eje1/bloque-e`, sin push. Pre-registro de E5 commiteado antes de correr "
          f"(`{_commit('docs/parada_tecnica/E5_PREREGISTRO.md')}`, "
          "`docs/parada_tecnica/E5_PREREGISTRO.md`), junto con "
          "`E4_RESPUESTA_ClaudeChat_2026-10-08.md`. Los resultados de E4 quedan como están. "
          "Detalle de la corrida: `docs/parada_tecnica/p3_equipos.md` y `p3_equipos.json`; "
          "figura: `docs/parada_tecnica/p3_maduracion_equipos.png`.", "",
          "## Qué se corrió", "",
          "Seis equipos DAG con las reglas de E5: Bias Auditor sin estados, exploración en WIO "
          "solo para el Explainer y Si del Explainer tipo · destinatario. A es el flujo de E4; "
          "B recibe colaboración de A rol por rol al nacer; B0 procesa los mismos casos sin "
          "compartir; BC procesa los mismos casos y coopera con C en Novice; N es el SAR "
          "neutro de L-3. Los estados se ganan: ninguno se fija a mano.", "",
          "## Colaboración A → B", ""]
    for x in d["colaboracion"]:
        c = x["conteo"]
        L.append(f"- **{TITULO[x['rol']]}** ({x['estados']['donante']} → "
                 f"{x['estados']['receptor']}): {'aceptada' if x['aceptada'] else 'rechazada'}; "
                 f"{c['igual']} iguales, {c['similar']} similares, {c['nueva']} nuevas; base de B "
                 f"{x['base_receptor_antes']} → {x['base_receptor_despues']}; ΣP = K en B: "
                 f"{'sí' if x['invariante_receptor'] else 'no'}; LCB de Ω sobre A "
                 f"{num(x['omega'][x['donante']]['lcb'], 3)}.")
    L += ["", "## Cooperación BC ↔ C", ""]
    for r, c in d["cooperacion"].items():
        acept = next((x for x in c["intentos"] if x["aceptada"]), None)
        esperas = ", ".join(f"{w['ventana']} (C en {w['estado_C']})" for w in c["bc_en_novice"])
        if acept:
            k = acept["conteo"]
            L.append(f"- **{TITULO[r]}:** aceptada al cierre de {acept['ventana']} ("
                     f"{k['igual']} iguales, {k['similar']} similares, {k['nueva']} nuevas; "
                     f"ΣP = K en los dos: "
                     f"{'sí' if acept['invariante_receptor'] and acept['invariante_donante'] else 'no'}).")
        else:
            L.append(f"- **{TITULO[r]}:** no hubo cooperación. Ventanas con BC en Novice: "
                     f"{esperas or 'ninguna'}; el rol de C nunca estuvo en Novice en esas "
                     "ventanas (axioma [a]).")
    L += ["", "## ¿B madura antes que B0?", "",
          "Ciclo del rol en que gana cada estado (en los roles por caso, casos procesados):", "",
          "| Rol | Estado | A | B | B0 | BC | C |", "|---|---|---|---|---|---|---|"]
    for r in roles:
        for a in ESTADOS:
            L.append(f"| {TITULO[r]} | {a} | " + " | ".join(_c(_ciclo(m[e][r], a))
                                                          for e in ("A", "B", "B0", "BC", "C"))
                     + " |")
    L += ["", "| Rol | Ciclos exitosos (B · B0 · BC · N) | Teorías nuevas propias (B · B0 · BC "
          "· N) |", "|---|---|---|"]
    for r in roles:
        L.append(f"| {TITULO[r]} | " + " · ".join(str(m[e][r]["ciclos_exitosos"])
                                                 for e in ("B", "B0", "BC", "N"))
                 + " | " + " · ".join(str(m[e][r]["teorias_nuevas"])
                                     for e in ("B", "B0", "BC", "N")) + " |")
    L += ["", f"La región 7 se evalúa al cierre de cada intervalo de {cv['n_intervalo']} "
          f"ciclos, así que lo más rápido posible es Novice en el ciclo {cv['n_intervalo']}, "
          f"Trained en el {2 * cv['n_intervalo']} y Mature en el {3 * cv['n_intervalo']}.", "",
          "## Cálculo literal de L-3 entre configuraciones", "",
          "En la tesis, los porcentajes se determinan comparando configuraciones de SAR (Anexo "
          "L-3, Tablas L-16 y L-17). Para decidir la promoción de un agente individual durante su "
          "actuación se operacionalizan como en P1; acá se calculan como en la fuente, entre "
          "configuraciones que procesan los mismos casos (N, B0, B y BC; mínimo = N).", "",
          "| Rol | Evaluada | %CEA | %RCE | %TNA | %RTN | Evoluciona |",
          "|---|---|---|---|---|---|---|"]
    for r, f in d["l3"].items():
        for ev, x in f["evaluadas"].items():
            L.append(f"| {TITULO[r]} | {ev} | {num(x['pct_cea'], 1)} | {num(x['pct_rce'], 1)} | "
                     f"{num(x['pct_tna'], 1)} | {num(x['pct_rtn'], 1)} | "
                     f"{'sí' if x['evoluciona'] else 'no'} |")
    L += ["", "**Nota técnica para conversar con Jorge.** Con estas definiciones, %TNA ≤ %RTN "
          "equivale a «promedio de teorías nuevas ≤ máximo», y %CEA ≥ %RCE, a «ciclos exitosos "
          "de la configuración evaluada ≥ promedio de las configuraciones». Con B, que no generó "
          "teorías propias en el Parser ni en el Explainer, %TNA = %RTN = 100.", "",
          "## Equidad por rol", ""]
    nr = m["N"]["parser"]["tasa_favorable"]
    defs = defectos_por_grupo(cfg, "B", cfg["equipo_e5"]["muestreo_e4"]["semillas_extra"])
    dx = defs["extra"]
    defs = defs["flujo"]
    brecha_bio = abs(pre["parser"]["por_grupo"]["AR"]["p_completo_operador_bio"]
                     - pre["parser"]["por_grupo"]["no-AR"]["p_completo_operador_bio"])
    L += [f"- **Canal proxy del Parser.** Con el operador BIO (neutro N), la completitud fue "
          f"{num(nr['AR'], 3)} (AR) y {num(nr['no-AR'], 3)} (no-AR): brecha "
          f"{num(m['N']['parser']['brecha_favorable'], 3)} (esperada por el pre-registro de E4: "
          f"{num(brecha_bio, 3)}). Con aprendizaje, la brecha de toda la corrida fue "
          f"{num(m['B']['parser']['brecha_favorable'], 3)} en B y "
          f"{num(m['B0']['parser']['brecha_favorable'], 3)} en B0; fair(W) del Parser en las "
          "tres primeras ventanas: B " + ", ".join(num(x["fair_w"], 1)
                                                   for x in m["B"]["parser"]["fair_w"][:3])
          + "; B0 " + ", ".join(num(x["fair_w"], 1) for x in m["B0"]["parser"]["fair_w"][:3])
          + ". Lo que queda son los documentos con defecto (regla 7): en este flujo, "
          f"{defs['AR']['defectos']}/{defs['AR']['casos']} en AR y "
          f"{defs['no-AR']['defectos']}/{defs['no-AR']['casos']} en no-AR (Fisher p = "
          f"{num(defs['p_fisher'], 4)}). Es otra diferencia de la semilla: en "
          f"{cfg['equipo_e5']['muestreo_e4']['semillas_extra']} semillas más del mismo "
          f"generador, {num(100 * dx['AR']['defectos'] / dx['AR']['casos'], 1)} % y "
          f"{num(100 * dx['no-AR']['defectos'] / dx['no-AR']['casos'], 1)} % (p = "
          f"{num(dx['p_fisher'], 4)}). Esto no es evidencia de la conjetura de atenuación.",
          "- **fair(W) media · mínimo por rol** (B · B0): " + "; ".join(
              f"{TITULO[r]} {num(m['B'][r]['fair_w_media'], 3)} · {num(m['B'][r]['fair_w_min'], 1)}"
              f" frente a {num(m['B0'][r]['fair_w_media'], 3)} · {num(m['B0'][r]['fair_w_min'], 1)}"
              for r in roles) + ". El Bias Auditor no derivó ninguna ventana en ningún equipo "
          "(ventana de 20; decisión 2).", "",
          "## Celdas nunca resueltas", ""]
    for e in ("A", "B", "B0", "BC", "C"):
        partes = []
        for r in roles:
            cs = m[e][r]["celdas_nunca_resueltas"]
            partes.append(f"{TITULO[r]} {len(cs)}"
                          + (f" ({sum(x['fracasos'] for x in cs)} fracasos)" if cs else ""))
        L.append(f"- **{e}:** " + "; ".join(partes) + ".")
    e4_exp = p4["celdas_sin_exito_en_wio"]["explainer"]
    L += [f"- El Explainer de A, con las reglas de E5, no tiene celdas nunca resueltas; en E4 "
          f"tenía {len(e4_exp)} ({e4_exp[0]['ciclos'] if e4_exp else 0} fracasos en WIO). Es el "
          "hallazgo que motivó la decisión 3.", "",
          "## Pedido sobre el resultado 5 de E4", ""]
    f, x = mu["flujo_e4"], mu["semillas_extra"]
    L += [f"Calificados en el flujo de E4: {num(f['tasas']['AR'], 3)} (AR) y "
          f"{num(f['tasas']['no-AR'], 3)} (no-AR). z = {num(f['z'], 2)}; Fisher exacto p = "
          f"{num(f['p_fisher_bilateral'], 4)}; permutación p = {num(f['p_permutacion'], 4)}. En "
          f"{x['n']} semillas más, la diferencia media es {num(x['diferencia_media'], 4)} y solo "
          f"{num(100 * x['fraccion_abs_mayor_o_igual_que_e4'], 1)} % de las semillas tiene una "
          "diferencia de igual o mayor tamaño. Con todas juntas, el grupo es independiente de la "
          f"verdad (Fisher p = {num(x['juntas']['p_fisher_grupo_verdad'], 4)}) y de la celda de "
          f"Si (χ² p = {num(x['juntas']['independencia_grupo_celda']['p'], 4)}). Detalle: "
          "`docs/parada_tecnica/e4_muestreo_calificados.md`. La semilla no se cambió.", "",
          "## Resultados que no fueron los esperados", ""]
    mb, mb0 = m["B"]["matcher"], m["B0"]["matcher"]
    ev_b, ev_b0 = mb["evaluaciones"][0], mb0["evaluaciones"][0]
    L += [f"1. **El Matcher de B gana Novice y Trained más tarde que el de B0** (Novice en el "
          f"ciclo {_c(_ciclo(mb, 'Novice'))} frente a {_c(_ciclo(mb0, 'Novice'))}; Trained en "
          f"el {_c(_ciclo(mb, 'Trained'))} frente a {_c(_ciclo(mb0, 'Trained'))}), **pero llega "
          f"a Mature** (ciclo {_c(_ciclo(mb, 'Mature'))}) y el de B0 queda en "
          f"{mb0['estado_final']}. En la primera evaluación, B acertó {ev_b['ce_a']} de "
          f"{cv['n_intervalo']} frente a {ev_b0['ce_a']} de B0, pero su CE_0 fue {ev_b['ce_0']} "
          f"frente a {ev_b0['ce_0']}: %CEA {num(ev_b['pct_cea'], 1)} frente a "
          f"{num(ev_b0['pct_cea'], 1)}. CE_0 es el operador BIO sobre la Si que le llega al "
          "Matcher, y en B esa Si viene de un Parser que ya extrae bien desde el primer caso "
          "(recibió las teorías de A). Un Parser mejor sube el punto de comparación del Matcher. "
          f"En toda la corrida, el Matcher de B acertó {mb['ciclos_exitosos']} frente a "
          f"{mb0['ciclos_exitosos']} de B0.",
          "2. **Parser y Explainer ganan cada estado en el primer cierre posible en todos los "
          "equipos** (B, B0, BC y C), así que la colaboración no puede adelantarlos: el efecto "
          "se ve en los aciertos y en las teorías nuevas, no en los ciclos hasta cada estado.",
          f"3. **El Matcher de C nunca sale de Born** (agota los {cv['ciclos_por_capa']['BIO']} "
          "ciclos de BIO con %CEA " + ", ".join(num(e["pct_cea"], 1)
                                              for e in m["C"]["matcher"]["evaluaciones"])
          + f"). Por eso no hubo cooperación del Matcher, y el Matcher de BC es el mismo que el "
          f"de B0 ({m['BC']['matcher']['ciclos_exitosos']} y "
          f"{m['B0']['matcher']['ciclos_exitosos']} ciclos exitosos). En L-3 con BC como "
          "configuración evaluada, el Matcher no cumple %CEA ≥ %RCE.",
          "4. **La colaboración no cierra el canal proxy del Parser antes que B0:** B0 lo cierra "
          "por sí solo en el primer intervalo; la brecha que queda en los dos viene de los "
          "documentos con defecto de esta semilla (ver «Equidad por rol»).",
          f"5. **La semilla de E4 es poco frecuente** (p ≈ {num(f['p_fisher_bilateral'], 2)}): "
          "la brecha de paridad del Matcher en E4 viene de una diferencia de calificados que "
          "aparece en pocas semillas.", "",
          "## Preguntas para Claude chat (y, si corresponde, para la dirección)", "",
          "1. **Punto de comparación de %CEA dentro de un equipo** (resultado 1). Hoy CE_0 es el "
          "operador BIO sobre la Si que le llega al rol, así que el aprendizaje de un rol de "
          "arriba sube la vara del de abajo. ¿Se mantiene (es el contrafáctico pre-registrado) "
          "o, para comparar equipos, se informa también contra el equipo neutro N?",
          "2. **Efecto techo de la promoción por intervalos** (resultado 2). Con n = 20, Parser "
          "y Explainer ya promueven en cada primer cierre posible sin compartir. ¿Se informa así, "
          "o se agrega una métrica de maduración que no tenga piso (por ejemplo, ciclos hasta "
          "una tasa de aciertos dada)? No se cambia nada sin decisión.",
          "3. **Cooperación del Matcher** (resultado 3). No se cambia la semilla de C. ¿Se "
          "informa tal cual?",
          "4. **E6:** se sigue con la condición de control con sesgo programado pre-registrada en "
          "E4_RESPUESTA (decisión 2), salvo indicación en contrario.", "",
          "## Qué sigue", "",
          "E6 (métricas de equidad por rol, con la condición de sesgo programado) y E7 (informe y "
          "cierre). **Frenado en el punto de control de E5.** Sin push.", ""]
    ruta = base / "E5_PUNTO_DE_CONTROL.md"
    ruta.write_text("\n".join(L) + "\n", encoding="utf-8")
    return str(ruta)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Informe del punto de control de E5")
    ap.add_argument("--out", default=None)
    ap.add_argument("--correr", action="store_true", help="corre P3 y el muestreo antes")
    a = ap.parse_args()
    if a.correr:
        import e4_muestreo
        import p3_equipos_dag
        p3_equipos_dag.correr(a.out)
        e4_muestreo.correr(a.out)
    print(escribir(a.out))
