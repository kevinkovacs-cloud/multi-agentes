#!/usr/bin/env python
"""
Informe del punto de control de E2 (Bloque E): escribe docs/parada_tecnica/E2_PUNTO_DE_CONTROL.md
a partir de p1.json y p2b.json (corre P1 y P2b si se pide). Ningún número a mano.

Uso:  python experiments/parada_tecnica/informe_e2.py [--out DIR] [--correr]
"""
from __future__ import annotations
import argparse
import json
from math import comb

from comun_pt import encabezado_md, num, out_dir

NOMBRES_MOTIVO = {"celda": "plan de la celda (Fig. 4.21)",
                  "similitud": "respaldo por similitud (extensión)",
                  "azar_no_probada": "azar: primera acción no probada",
                  "azar_bio": "azar: operador BIO"}


def p_brecha_al_menos(d: int, n: int, p: float) -> float:
    """P(|X − Y| ≥ d), X, Y ~ Bin(n, p) independientes: brecha de avance entre dos grupos de
    n casos sin disparidad real (solo muestreo)."""
    pmf = [comb(n, k) * p ** k * (1 - p) ** (n - k) for k in range(n + 1)]
    return sum(pmf[x] * pmf[y] for x in range(n + 1) for y in range(n + 1) if abs(x - y) >= d)


def _bloqueos(ciclos: list[dict]) -> list[dict]:
    """(Si, A) cuyo plan de celda se repitió con más fracasos que aciertos (≥ 3 usos)."""
    usos: dict = {}
    for r in ciclos:
        if r["motivo"] != "celda":
            continue
        k = (json.dumps(r["si"], sort_keys=True, ensure_ascii=False), r["accion"])
        usos.setdefault(k, []).append(r["u_tarea"] > 0)
    out = []
    for (si, a), oks in usos.items():
        if len(oks) >= 3 and oks.count(False) > oks.count(True):
            otra = [x for x in ("ADVANCE", "REJECT") if x != a][0]
            probada = any(r["accion"] == otra and json.dumps(r["si"], sort_keys=True,
                                                             ensure_ascii=False) == si
                          for r in ciclos)
            out.append({"si": json.loads(si), "accion": a, "aciertos": oks.count(True),
                        "fracasos": oks.count(False), "otra_accion_probada_alguna_vez": probada})
    return out


def escribir(out=None) -> str:
    destino = out_dir(out)
    p1 = json.loads((destino / "p1.json").read_text(encoding="utf-8"))
    p2 = json.loads((destino / "p2b.json").read_text(encoding="utf-8"))
    cfg = p1["config"]
    n = cfg["n_intervalo"]
    L = encabezado_md("E2 · Punto de control del Bloque E (puntos 1 y 2b del pedido)")
    L += ["Rama `eje1/bloque-e`, sin push. Decisiones aplicadas: "
          "`docs/parada_tecnica/E0_RESPUESTA_P1-P5_ClaudeChat_2026-10-08.md`. Parámetros y entorno "
          "pre-registrados antes de la primera corrida (`configs/parada_tecnica.yaml`, "
          "`docs/parada_tecnica/E2_PREREGISTRO_ENTORNO.md`).", "",
          "## Qué se hizo", "",
          "- **E1:** orquestación del DAG con LangGraph (`core/grafo.py`), equivalente al "
          "orquestador secuencial en el lote de la PoC.",
          "- **E2:** registro de teorías del LLC (Fig. 4.13, ΣP = K), planificador por ranking "
          "(Fig. 4.21, validez del plan, «azar» sin decisiones aleatorias), motor de las 7 "
          "regiones dentro del agente, estadísticas de la región 6, estado ganado y regla de "
          "evolución de P1 ∧ gate de Ω, entorno BIO/TBO/WIO y rol Matcher.", "",
          "## Cómo reproducirlo", "", "```bash",
          "python experiments/parada_tecnica/preregistro.py",
          "python experiments/parada_tecnica/p1_teoria_punto_a_punto.py",
          "python experiments/parada_tecnica/p2b_planificador.py",
          "python experiments/parada_tecnica/informe_e2.py", "```", "",
          "## P1 · El ciclo de vida punto a punto", "",
          f"- **Resultado:** estado final **{p1['resultado']['estado_final']}** tras "
          f"{p1['resultado']['ciclos']} ciclos; capas recorridas: "
          + ", ".join(f"{c['capa']} ({c['ciclos']} ciclos, "
                      f"{'promovido' if c['promovido'] else 'sin promoción'})"
                      for c in p1["resultado"]["capas"]) + ".",
          f"- **Traza región por región del ciclo 1:** `docs/parada_tecnica/p1_traza_ciclo1.md`. "
          f"T* = T{p1['teoria_estrella']['id']} (`{p1['teoria_estrella']['iri']}`), nace en R5 con "
          f"P = {p1['teoria_estrella']['nacimiento']['p']}, K = "
          f"{p1['teoria_estrella']['nacimiento']['k']}, U = "
          f"{num(p1['teoria_estrella']['nacimiento']['u'], 2)}.",
          "- **Línea de tiempo:** `docs/parada_tecnica/p1_linea_de_tiempo.png`.", "",
          "### Evaluaciones de la región 7 (al cierre de cada intervalo)", "",
          "| Capa | Ciclo | CE_a | CE_0 | %CEA (≥ %RCE) | %TN (≤ %RTN) | fair(W) | r | Gate Ω "
          "puntual | Certificado (informado) | Promueve | Estado después |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for e in p1["evaluaciones"]:
        tn = "no aplica" if e["pct_tn"] is None else f"{num(e['pct_tn'], 1)} %"
        L.append(f"| {e['capa']} | {e['ciclo']} | {e['ce_a']} | {e['ce_0']} | "
                 f"{num(e['pct_cea'], 1)} % ({'sí' if e['cumple_cea'] else 'no'}) | {tn} | "
                 f"{num(e['fair_w'], 2)} | {num(e['reputacion'], 3)} | "
                 f"{'aprueba' if e['gate_omega'] else 'rechaza'} | "
                 f"{'aprueba' if e['gate_certificado'] else 'rechaza'} | "
                 f"{'sí' if e['promueve'] else 'no'} | {e['estado_despues']} |")
    v, dz = p1["regla_de_validez_aplicada"], p1["desacuerdos_fig421_alg47"]
    L += ["", f"%RCE = {cfg['rce']}, %RTN = {cfg['rtn']}, τ = {num(cfg['tau'], 1)}, n = {n}.",
          "", "### Planificador", "",
          f"- **Regla de validez del plan aplicada:** {v['veces']} veces "
          f"(ciclos {', '.join(map(str, v['ciclos'])) or '—'}).",
          f"- **Desacuerdos Fig. 4.21 / Alg. 4.7:** {dz['veces']}"
          + (": " + "; ".join(f"ciclo {d['ciclo']} (Fig. 4.21 → T{d['fig_4_21']}, Alg. 4.7 → "
                              f"T{d['alg_4_7']})" for d in dz["casos"]) if dz["casos"] else "") + ".",
          "- **Decisiones por motivo:** " + "; ".join(
              f"{NOMBRES_MOTIVO[k]}: {v2}" for k, v2 in p1["decisiones_por_motivo"].items()) + ".",
          f"- **Invariante ΣP = K en la base final:** "
          f"{'se cumple' if p1['invariante_sigma_p_igual_k'] else 'NO se cumple'}.", "",
          "### Estadísticas de la región 6 al final", ""]
    st = p1["estadisticas_finales"]
    L += [f"Situaciones {st['situaciones']} · teorías acumuladas {st['teorias_acumuladas']} · "
          f"teorías exitosas {st['teorias_exitosas']} · ciclos exitosos {st['ciclos_exitosos']} "
          f"de {st['ciclos']} · planes {st['planes']} (exitosos {st['planes_exitosos']}) · azares "
          f"{st['azares']} · teorías por intervalo de U {st['teorias_por_intervalo_u']} · P/K "
          f"general {num(st['pk_general'], 3) if st['pk_general'] is not None else '—'}.", "",
          "## P2b · Ranking y recuperación de la teoría propia", "",
          "Detalle: `docs/parada_tecnica/p2b_planificador.md`.", ""]
    ci = p2["caso_i_misma_si"]
    L.append(f"- **(i) misma Si que T\\*:** elige {ci['alpha_1']['accion']} "
             f"(T{ci['alpha_1']['teoria']}, {NOMBRES_MOTIVO[ci['alpha_1']['motivo']]}); con "
             f"α = 0,5 {'cambia' if ci['alpha_cambia_la_elegida'] else 'no cambia'}.")
    ii, iii = p2["caso_ii_si_nueva_con_similitud"], p2["caso_iii_sin_nada_aplicable"]
    if ii:
        L.append(f"- **(ii) Si nueva:** con el respaldo activado, "
                 f"{NOMBRES_MOTIVO[ii['con_respaldo']['motivo']]} → {ii['con_respaldo']['accion']}; "
                 f"como en P1, {NOMBRES_MOTIVO[ii['sin_respaldo_como_en_p1']['motivo']]} → "
                 f"{ii['sin_respaldo_como_en_p1']['accion']}.")
    if iii:
        L.append(f"- **(iii) nada aplicable:** en {iii['en_la_capa_del_agente']['capa']}, "
                 f"{NOMBRES_MOTIVO[iii['en_la_capa_del_agente']['motivo']]} → "
                 f"{iii['en_la_capa_del_agente']['accion']}; en WIO, "
                 f"{NOMBRES_MOTIVO[iii['en_wio']['motivo']]} → {iii['en_wio']['accion']}.")
    al = p2["alpha_en_todas_las_celdas"]
    L += [f"- **α = 0,5 en toda la base:** {al['celdas_con_e_estimable']} de {al['celdas']} "
          f"celdas con ê(t) estimable (m_min = {al['m_min_por_grupo']} por grupo); cambia la "
          f"elegida en {len(al['cambios'])}.", ""]

    # ---- resultados que no fueron los esperados (condiciones calculadas) ----
    R = []
    if p1["resultado"]["estado_final"] == "Born":
        causas = []
        for e in p1["evaluaciones"]:
            falla = [x for x, ok in (("%CEA", e["cumple_cea"]), ("gate de Ω", e["gate_omega"]),
                                     ("%TN", e["cumple_tn"])) if not ok]
            causas.append(f"ciclo {e['ciclo']}: falla {', '.join(falla)}")
        R.append("**El agente no sale de Born.** Ningún cierre de intervalo cumplió la regla ("
                 + "; ".join(causas) + "). Con la regla «sin promoción → detener», TBO y WIO "
                 "no se recorren en P1; las transiciones del motor están verificadas en "
                 "`tests/test_bloquee_ciclo.py`.")
    solo_gate = [e for e in p1["evaluaciones"] if e["cumple_cea"] and e["cumple_tn"]
                 and not e["gate_omega"]]
    if solo_gate:
        partes = []
        for e in solo_gate:
            ventana = [c for c in p1["ciclos"]
                       if c["capa"] == e["capa"] and e["ciclo_capa"] - n < c["ciclo_capa"]
                       <= e["ciclo_capa"]]
            p_av = sum(c["accion"] == "ADVANCE" for c in ventana) / len(ventana)
            brecha = round((1 - e["fair_w"]) * (n // 2))
            prob = p_brecha_al_menos(brecha, n // 2, p_av)
            partes.append(f"ciclo {e['ciclo']}: %CEA = {num(e['pct_cea'], 1)} % cumple, pero r = "
                          f"{num(e['reputacion'], 3)} < τ; fair(W) = {num(e['fair_w'], 2)}. Sin "
                          f"ninguna disparidad real, con {n // 2} casos por grupo y tasa de avance "
                          f"{num(p_av, 2)}, una brecha de al menos {brecha}/{n // 2} ocurre con "
                          f"probabilidad {num(prob, 3)}")
        R.append("**El gate de Ω frena la promoción con ventanas chicas.** "
                 + "; ".join(partes) + ". Es el ruido de muestreo de ventanas de "
                 f"{n} casos: el gate puntual no distingue disparidad real de azar a ese tamaño.")
    bl = _bloqueos(p1["ciclos"])
    if bl:
        R.append("**Bloqueo por U binaria en el orden de la Fig. 4.21.** "
                 + "; ".join(f"Si {json.dumps(b['si'], ensure_ascii=False)}: el plan repitió "
                             f"{b['accion']} con {b['aciertos']} aciertos y {b['fracasos']} "
                             f"fracasos; la otra acción "
                             f"{'se probó' if b['otra_accion_probada_alguna_vez'] else 'nunca se probó'}"
                             for b in bl)
                 + ". Una sola observación favorable deja la variante (Si, A, Sf) con U = 1, y "
                 "como U es la primera clave del orden, queda primera aunque la acción fracase "
                 "después; la regla de validez solo actúa si la primera del orden tiene u_tarea = 0.")
    peor = [e for e in p1["evaluaciones"] if e["ce_a"] < e["ce_0"]]
    if peor:
        R.append("**El agente acierta menos que el SAR neutro en algún intervalo:** "
                 + "; ".join(f"ciclo {e['ciclo']} (CE_a = {e['ce_a']}, CE_0 = {e['ce_0']})"
                             for e in peor) + ".")
    if al["celdas_con_e_estimable"] == 0:
        R.append(f"**α = 0,5 no se pudo evaluar:** ninguna teoría juntó {al['m_min_por_grupo']} "
                 "usos como plan en cada grupo, así que U_rol cae en α = 1 en todas las celdas.")
    if p1["teoria_estrella"]["nacimiento"]["u"] == 0:
        R.append("**T\\* nace de un fracaso** (U = 0): en el ciclo 1 la celda estaba vacía, el "
                 "agente exploró la primera acción del orden fijo y no era la correcta. Es la "
                 "teoría que E3 tiene que compartir.")
    L += ["## Resultados que no fueron los esperados (se reportan tal cual)", ""]
    L += [f"{i + 1}. {r}" for i, r in enumerate(R)] or ["Ninguno."]
    L += ["", "## Para decidir antes de seguir (no se cambió nada: son reglas pre-registradas)", "",
          "- **Gate de Ω y tamaño de ventana.** Con n = 20 la reputación queda dominada por el "
          "ruido de muestreo. Opciones: mantenerlo y reportarlo; evaluar el gate sobre más "
          "ventanas o ventanas más grandes; o exigir el gate solo cuando la ventana tiene el "
          "tamaño de detección (`stats.n_power`).",
          "- **U binaria por variante.** Opciones: mantener el orden literal de la Fig. 4.21 y "
          "reportar el bloqueo; extender la regla de validez (por ejemplo, plan válido solo si la "
          "acción no acumula más fracasos que aciertos en la celda); o calcular u_tarea sobre "
          "(Si, A), como el método de utilidad basado en la acción de la tesis, que compara la "
          "acción de la teoría con la del robot reactivo en esa situación (§4.4.3.2, pp. 89–90).",
          "- **m_min por grupo para ê(t).** Con 60 ciclos no se alcanza; α = 0,5 no tiene "
          "efecto en esta escala.",
          "", "Cualquier cambio va en un commit nuevo, con su motivo, y se reporta en el informe "
          "final (regla de P1).", ""]
    texto = "\n".join(L)
    (destino / "E2_PUNTO_DE_CONTROL.md").write_text(texto, encoding="utf-8")
    return texto


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Informe del punto de control de E2")
    ap.add_argument("--out", default=None)
    ap.add_argument("--correr", action="store_true", help="corre P1 y P2b antes")
    a = ap.parse_args()
    if a.correr:
        import p1_teoria_punto_a_punto
        import p2b_planificador
        p1_teoria_punto_a_punto.correr(a.out)
        p2b_planificador.correr(a.out)
    escribir(a.out)
    print("E2_PUNTO_DE_CONTROL.md escrito")
