#!/usr/bin/env python
"""
Escribe docs/parada_tecnica/METRICAS_EQUIDAD_POR_ROL.md (documento para la dirección, punto 5)
desde las salidas de E6 (p5_metricas_equidad.json, p5_sesgo_programado.json), E6 v2
(p5_equidad_v2.json) y el control post hoc (p5_control_post_hoc.json). Ningún número a mano.
Terminología de E6_RESPUESTA (decisión 2): paridad demográfica, paridad de aciertos, odds
igualadas y, a nivel de celda, paridad de tasa de error.

Uso:  python experiments/parada_tecnica/metricas_equidad_doc.py [--out DIR]
"""
from __future__ import annotations
import argparse
import json

from comun_pt import cargar_config, encabezado_md, mayus, num, out_dir

TITULO = {"parser": "Parser", "matcher": "Semantic Matcher", "bias_auditor": "Bias Auditor",
          "explainer": "Explainer"}
ROTULO_PROG = "parámetros programados"
ROTULO_IV = "ilustra el mecanismo; no es evidencia de la conjetura de atenuación"


def _j(base, nombre):
    return json.loads((base / nombre).read_text(encoding="utf-8"))


def _n(x, nd=3) -> str:
    return "—" if x is None else num(x, nd)


def escribir(out=None) -> str:
    base = out_dir(out)
    cfg = cargar_config()
    m_min = cfg["utilidad"]["m_min_por_grupo"]
    c1, c2 = _j(base, "p5_metricas_equidad.json"), _j(base, "p5_sesgo_programado.json")
    v2, ctl = _j(base, "p5_equidad_v2.json"), _j(base, "p5_control_post_hoc.json")
    a1, a5 = c1["alpha_1.0"]["roles"], c1["alpha_0.5"]["roles"]
    r2 = v2["corrida_1"]["roles"]
    bq = c1["calificados_del_flujo"]
    p2 = a1["matcher"]["primeros_260"]
    L = encabezado_md("Métricas de equidad por rol (punto 5 del pedido)")
    L += ["Documento para la dirección. Lo generan `experiments/parada_tecnica/"
          "metricas_equidad_doc.py` y las salidas de E6 (pre-registro `E6_PREREGISTRO.md`), E6 v2 "
          "(pre-registro corto `E6_PREREGISTRO_v2.md`) y el control post hoc. Selección de "
          "personal es el dominio de experimentación.", "",
          "**Planos.** El plano de decisión es lo que el rol percibe y hace (Si, A, Sf). El grupo "
          "vive solo en el plano de auditoría (Ω y los registros E): nunca entra en Si, A ni los "
          "prompts (DE-4). Toda brecha entre grupos se calcula en ese plano.", "",
          "## Tres criterios que no coinciden", "",
          "- **Paridad demográfica:** diferencia de la tasa de resultado favorable entre grupos. "
          "Sigue a la tasa base: si un grupo tiene más calificados, la marca aunque las decisiones "
          "sean correctas.",
          "- **Paridad de aciertos:** diferencia de la tasa de decisiones correctas entre grupos.",
          "- **Odds igualadas (EO):** max(|ΔTPR|, |ΔFPR|): si entre los calificados (TPR) y entre "
          "los no calificados (FPR) cada grupo recibe el mismo trato.",
          "- **Paridad de tasa de error** (nivel celda): con la acción fija en una celda, TPR y FPR "
          "son triviales (todos los calificados de la celda reciben la misma acción); lo único no "
          "trivial es si la acción se equivoca más con un grupo. Es la base de ê(Si, A).", "",
          f"Ejemplo corrido (los 260 casos de E4): paridad demográfica "
          f"{num(p2['paridad_demografica']['brecha'], 3)}; aciertos "
          f"{num(p2['aciertos_por_grupo']['tasas']['AR'], 3)} (AR) y "
          f"{num(p2['aciertos_por_grupo']['tasas']['no-AR'], 3)} (no-AR); TPR "
          f"{num(p2['odds_igualadas']['tpr']['AR'], 3)} y {num(p2['odds_igualadas']['tpr']['no-AR'], 3)}"
          f" (EO {num(p2['odds_igualadas']['eo'], 3)}). «Los tres criterios no coinciden y "
          "responden preguntas distintas.» En los 600 casos de E6: paridad demográfica "
          f"{num(a1['matcher']['favorable']['brecha'], 3)} con diferencia de calificados "
          f"{num(bq['brecha'], 3)}; aciertos {num(a1['matcher']['aciertos_por_grupo']['tasas']['AR'], 3)}"
          f" y {num(a1['matcher']['aciertos_por_grupo']['tasas']['no-AR'], 3)}; EO "
          f"{num(a1['matcher']['odds_igualadas']['eo'], 3)}.", "",
          "## Métrica de cada rol", ""]
    filas = {
        "parser": ("Brecha de completitud entre grupos (resultado favorable = perfil completo); "
                   "como auditoría, el d_TV del canal proxy (cota inferior, B3).",
                   "|P(completo | AR) − P(completo | no-AR)|; d̂_TV = max(0, 2·bAcc − 1) de un "
                   "clasificador grupo ~ Si del Parser, en held-out.",
                   "Sf del Parser (decisión); grupo (auditoría).",
                   "Mezcla la estrategia con lo que trae el documento (defectos de la semilla). "
                   "El d_TV es una cota inferior, no el valor."),
        "matcher": ("A nivel rol y ventana: odds igualadas. A nivel celda (en la utilidad): "
                    "paridad de tasa de error, ê(Si, A). La paridad demográfica se informa para "
                    "contrastar.",
                    "EO = max(|ΔTPR|, |ΔFPR|), con la etiqueta observada (BIO y TBO: etiqueta del "
                    "escenario; WIO: revisión humana). ê(Si, A) = 1 − |err(AR) − err(no-AR)| "
                    "sobre E(Si, A).",
                    "Acción y Sf (decisión); grupo (auditoría).",
                    "La acción de la teoría es la decisión: dentro de una celda todos reciben la "
                    "misma acción, así que la paridad demográfica por celda es trivial. La "
                    "disparidad de trato surge de qué celdas y teorías se aplican a cada grupo y "
                    "se mide en la ventana. En WIO la etiqueta es la revisión humana, que puede "
                    "equivocarse."),
        "bias_auditor": ("Paridad de derivación Δ_esc (C5).",
                         "|P(derivado | AR) − P(derivado | no-AR)|.",
                         "Acción del Auditor y grupo de cada caso de la ventana (auditoría).",
                         "La derivación es por ventana: todos los casos reciben la misma "
                         "intervención y Δ_esc es 0 por construcción mientras las ventanas tengan "
                         "los dos grupos por igual. U_rol no aplica: la acción la decide la regla "
                         "(DE-6)."),
        "explainer": ("Brecha de completitud de la explicación entre grupos.",
                      "|P(completa | AR) − P(completa | no-AR)|.",
                      "Sf del Explainer (decisión); grupo (auditoría).",
                      "La completitud depende del tipo de decisión y del destinatario; si las "
                      "decisiones difieren por grupo, la brecha lo arrastra."),
    }
    for r, (d, f, pl, lim) in filas.items():
        x = a1[r]
        L += [f"### {TITULO[r]}", "", f"- **Definición:** {d}", f"- **Fórmula:** {f}",
              f"- **Datos y plano:** {pl}",
              "- **m_min:** " + ("no aplica." if r == "bias_auditor" else
                                 f"{m_min} lecturas por grupo para ê."),
              f"- **Límites:** {lim}",
              f"- **Valores (600 casos, α = 1):** brecha del resultado favorable "
              f"{_n(x['favorable']['brecha'])} (AR {_n(x['favorable']['tasas'].get('AR'))}, "
              f"no-AR {_n(x['favorable']['tasas'].get('no-AR'))})"
              + (f"; d_TV del canal proxy {_n(x['dtv_canal_proxy'])}" if r == "parser" else "")
              + (f"; odds igualadas {_n(x['odds_igualadas']['eo'])} (ΔTPR "
                 f"{_n(x['odds_igualadas']['delta_tpr'])}, ΔFPR "
                 f"{_n(x['odds_igualadas']['delta_fpr'])})" if r == "matcher" else "") + ".", ""]
    tot1 = {k: sum(a5[r]["alpha_0_5"][k] for r in ("parser", "matcher", "explainer"))
            for k in ("eleccion_cambiada", "accion_cambiada", "elegida_sin_e_frente_a_una_con_e")}
    L += ["## La equidad en la utilidad: U_rol con α = 0,5", "",
          f"U_rol = α·U + (1 − α)·ê; ê solo con al menos m_min = {m_min} lecturas en cada grupo.",
          "", "| Rol | v1 (ê por teoría): cambios de teoría · de acción | v2 (ê por celda): ajuste "
          "aplicado · no aplicable por falta de evidencia | v2: cambios de teoría · de acción |",
          "|---|---|---|---|"]
    for r in ("parser", "matcher", "explainer"):
        x1, aj, x2 = a5[r]["alpha_0_5"], r2[r]["ajuste_v2"], r2[r]["alpha_0_5"]
        L.append(f"| {TITULO[r]} | {x1['eleccion_cambiada']} · {x1['accion_cambiada']} | "
                 f"{aj['aplicado']} · {aj['no_aplicable_falta_evidencia']} (de "
                 f"{aj['con_candidatas']}) | {x2['eleccion_cambiada']} · {x2['accion_cambiada']} |")
    L += ["", f"- **v1** (E6): ê(t) por teoría. Cambió la teoría {tot1['eleccion_cambiada']} veces "
          f"y la acción {tot1['accion_cambiada']}: todas las variantes de una acción tienen la "
          f"misma U y ê(t) solo las reordenaba. En {tot1['elegida_sin_e_frente_a_una_con_e']} "
          "cambios ganó la variante sin ê: el respaldo premiaba la falta de evidencia.",
          "- **v2** (E6 v2): ê(Si, A) sobre todas las decisiones en que se aplicó A en Si; si "
          "alguna acción candidata no tiene ê, α = 1 para todas. No cambió ninguna acción ni "
          "ninguna teoría en estas corridas. Cuando hubo evidencia para comparar, la diferencia de "
          "U entre acciones fue mayor que la de ê; en la mayoría de las planificaciones faltó "
          "evidencia sobre la acción no elegida, porque una vez aprendida la acción la otra deja "
          "de probarse. Un test (`tests/test_bloquee_e6_v2.py`) muestra que con evidencia en las "
          "dos acciones y U parecidas el ajuste sí cambia la acción.",
          ("- Los aciertos y las tasas favorables por grupo de cada rol quedaron iguales con "
           "α = 1, v1 y v2." if all(a1[r]["aciertos"] == a5[r]["aciertos"] == r2[r]["aciertos"]
                                    and a1[r]["favorable"] == a5[r]["favorable"]
                                    == r2[r]["favorable"] for r in a1)
           else "- Los aciertos o las tasas por grupo cambian entre α = 1, v1 y v2: ver "
                "`p5_equidad_v2.md`."),
          "", "**Advertencia.** Dentro de una celda con la acción fija, ê(Si, A) mide si esa acción "
          "se equivoca más con un grupo que con el otro, lo que pasa cuando la Si no captura algo "
          "relacionado con el grupo. No mide trato desigual: ese se ve en la ventana.", "",
          f"## Condición con sesgo programado («{ROTULO_PROG}»)", "",
          "El sesgo entra por el rasgo proxy `titulo_local` en la Si del Matcher (regla 11): se "
          "correlaciona con el grupo y no con la verdad; el operador BIO lo penaliza.", ""]
    for mag, f in c2.items():
        if mag in ("rotulo_programado", "rotulo_atenuacion", "calificados_del_flujo", "figura",
                   "demo", "rotulos"):
            continue
        cf = f["configuraciones"]
        ne, al = cf["neutro"], cf["alpha_1"]
        der = ne["ventanas_derivadas_regla_acumulada"]
        aj = v2["corrida_2"][mag]["ajuste_v2"]
        sl = al["teorias_sin_titulo_local"]
        L.append(f"- **{mag.replace('_', ' ').capitalize()}** (brecha del operador "
                 f"{num(f['brecha_operador_esperada'], 2)}; d_TV de la Si frente al grupo "
                 f"{_n(f['dtv_si_matcher'])}): paridad demográfica neutro "
                 f"{_n(ne['brecha_toda_la_corrida'])} y Matcher que aprende "
                 f"{_n(al['brecha_toda_la_corrida'])}; odds igualadas {_n(ne['odds_igualadas']['eo'])}"
                 f" y {_n(al['odds_igualadas']['eo'])}. Regla de ventana: ninguna derivación; "
                 f"regla acumulada: {len(der)} ventanas del neutro"
                 + (f" (desde {der[0]})" if der else "") + ", "
                 f"{len(al['ventanas_derivadas_regla_acumulada'])} del Matcher que aprende. En "
                 f"E(t) de las celdas sin título local: {sl['lecturas_AR']} lecturas de AR y "
                 f"{sl['lecturas_no_AR']} de no-AR. E6 v2: ajuste aplicado en {aj['aplicado']} de "
                 f"{aj['con_candidatas']} planificaciones.")
    L += ["", f"Atenuación por aprendizaje: {ROTULO_IV}.", "",
          "**Límite del gate de compartición** (decisión 3 de E6_RESPUESTA). El gate usa la brecha "
          "del resultado favorable, que a nivel rol es paridad demográfica: no separa la tasa base "
          "del sesgo, frena de más cuando las tasas base difieren y no ve un sesgo por debajo de lo "
          "detectable. En la condición detectable "
          + ("dejó pasar" if c2["detectable"]["configuraciones"]["alpha_1"]["comparticion"]
             ["aceptada"] else "frenó")
          + " la colaboración del Matcher sesgado que aprende (LCB "
          + _n(c2["detectable"]["configuraciones"]["alpha_1"]["comparticion"]["omega_donante"]
               ["lcb"])
          + "), según el estándar de evidencia acordado. Propuesta para después "
          "de la parada técnica, sin implementar: que el gate use la métrica del rol (odds "
          "igualadas para el Matcher).", "",
          "**Alerta de proxy para revisión humana** (propuesta, sin implementar). El d_TV de la Si "
          "frente al grupo (B3) ya existe y dio "
          f"{_n(c2['detectable']['dtv_si_matcher'])} en la condición detectable: la Si deja "
          "inferir el grupo. Se propone mostrarlo como alerta del Monitor de Equidad, no como gate.",
          "", "## Control post hoc", ""]
    k = ctl["control"]
    L += [f"«{mayus(ctl['rotulo'])}». Un Matcher que aprende sobre los mismos casos de la "
          "condición programada, sin el rasgo y con el operador BIO sin sesgo (el de P1), α = 1. "
          "Descriptivo: no cambia ninguna regla ni conclusión pre-registrada.", "",
          "| Matcher (α = 1) | Estado final | Paridad demográfica | Odds igualadas | Aciertos AR / "
          "no-AR | Decisiones del operador BIO |", "|---|---|---|---|---|---|",
          f"| control sin sesgo | {k['estado_final']} | {_n(k['brecha_toda_la_corrida'])} | "
          f"{_n(k['odds_igualadas']['eo'])} | {_n(k['aciertos_por_grupo']['tasas']['AR'])} / "
          f"{_n(k['aciertos_por_grupo']['tasas']['no-AR'])} | "
          f"{num(100 * k['fraccion_operador_bio'], 1)} % |"]
    for mag, fr in ctl["frente_al_matcher_sesgado_que_aprende"].items():
        s = c2[mag]["configuraciones"]["alpha_1"]
        L.append(f"| sesgado, {mag.replace('_', ' ')} | {fr['estado_final']['sesgado']} | "
                 f"{_n(fr['paridad_demografica']['sesgado'])} | {_n(fr['odds_igualadas']['sesgado'])}"
                 f" | {_n(s['aciertos_por_grupo']['tasas']['AR'])} / "
                 f"{_n(s['aciertos_por_grupo']['tasas']['no-AR'])} | "
                 f"{num(100 * fr['fraccion_operador_bio']['sesgado'], 1)} % |")
    det = ctl["frente_al_matcher_sesgado_que_aprende"]["detectable"]
    L += ["", f"Diferencia de calificados del flujo: {num(bq['brecha'], 3)}. Con la magnitud "
          f"detectable, la paridad demográfica del Matcher sesgado supera a la del control en "
          f"{num(det['paridad_demografica']['diferencia'], 3)} y las odds igualadas en "
          f"{num(det['odds_igualadas']['diferencia'], 3)}. **El control no es un contrafáctico "
          f"limpio:** llegó a {k['estado_final']} y pasó la mayor parte del flujo en WIO, donde el "
          "Matcher no explora (P3) y el operador BIO decide en las celdas nuevas; los Matchers "
          "sesgados quedaron en capas con exploración. Por eso aciertan más. La diferencia mezcla el "
          "sesgo con la dinámica del ciclo de vida.", ""]
    ruta = base / "METRICAS_EQUIDAD_POR_ROL.md"
    ruta.write_text("\n".join(L) + "\n", encoding="utf-8")
    return str(ruta)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None)
    print(escribir(ap.parse_args().out))
