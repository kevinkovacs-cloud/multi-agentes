#!/usr/bin/env python
"""
Bloque E · E7: escribe docs/parada_tecnica/INFORME_PARADA_TECNICA.md (una sección por punto
del pedido de la dirección) y docs/parada_tecnica/LEEME_REUNION.md (guion para mostrar en
vivo), desde las salidas de todas las corridas. Ningún número a mano.

Uso:  python experiments/parada_tecnica/informe_final.py [--out DIR]
"""
from __future__ import annotations
import argparse
import json

from comun_pt import ROTULOS, cargar_config, encabezado_md, mayus, num, out_dir
from informe_e4 import _commit

S = "`python experiments/parada_tecnica/"
TITULO = {"parser": "Parser", "matcher": "Semantic Matcher", "bias_auditor": "Bias Auditor",
          "explainer": "Explainer"}


def _j(base, nombre):
    return json.loads((base / nombre).read_text(encoding="utf-8"))


def _n(x, nd=3) -> str:
    return "—" if x is None else num(x, nd)


def _promos(lista) -> str:
    return "; ".join(f"{p.get('estado_antes', p.get('de'))} → {p.get('estado_despues', p.get('a'))}"
                     f" en el ciclo {p['ciclo']}" for p in lista) or "ninguna"


def _rotulos() -> list[str]:
    return ["- **Rótulos:** " + " · ".join(f"«{mayus(r)}»" for r in ROTULOS) + "."]


def _si(si: dict) -> str:
    return ", ".join(f"{k} = {v}" for k, v in si.items())


def seccion_1(base) -> list[str]:
    p1, p1v1 = _j(base, "v2/p1.json"), _j(base, "v1/p1.json")
    t = p1["teoria_estrella"]
    prom = [e for e in p1["evaluaciones"] if e["promueve"]]
    est = p1["estadisticas_finales"]
    return [
        "## Punto 1 · Una teoría generada y el ciclo de vida punto a punto", "",
        "- **Qué se demuestra (mecanismo, en el entorno simulado):** un caso genera una teoría "
        "⟨Si, A, Sf, P, K, U⟩ en la región 5 del primer ciclo, y el agente recorre las siete "
        "regiones del LLC en cada ciclo (Ierache 2010, §4.2, pp. 61–64). El estado se gana con la "
        "regla de evolución (Fig. 4.28, p. 123, adaptada a un agente) y el gate de Ω.",
        f"- **Comando:** {S}p1_teoria_punto_a_punto.py --version v2` (y `--version v1`).",
        f"- **Números clave (v2):** la teoría T{t['id']} nace en el ciclo {t['nacimiento']['ciclo']} "
        f"(Si: {_si(t['si'])}; A = {t['a']}; Sf: calificado = {t['sf']['calificado']}; P "
        f"{t['nacimiento']['p']}, K {t['nacimiento']['k']}, U {num(t['nacimiento']['u'], 3)}). El "
        f"agente termina en **{p1['resultado']['estado_final']}** en {p1['resultado']['ciclos']} "
        f"ciclos: {_promos(prom)}. Al final: {est['teorias_acumuladas']} teorías, "
        f"{est['ciclos_exitosos']} ciclos exitosos, {est['azares']} «azares»; ΣP = K en todas las "
        f"celdas: {'sí' if p1['invariante_sigma_p_igual_k'] else 'no'}.",
        "- **Figuras y trazas:** `docs/parada_tecnica/v2/p1_linea_de_tiempo.png`, "
        "`docs/parada_tecnica/v2/p1_traza_ciclo1.md`, `docs/parada_tecnica/p1_gate_caracteristica.png`.",
        *_rotulos(),
        f"- **Resultados inesperados:** con la v1 el agente quedó en "
        f"**{p1v1['resultado']['estado_final']}** tras {p1v1['resultado']['ciclos']} ciclos: el gate "
        "puntual de Ω con ventanas de 20 era ruido de muestreo y la U binaria trababa la elección "
        "(`docs/parada_tecnica/E2_v1_vs_v2.md`).",
        f"- **Historial:** v1 (pre-registro `{_commit('docs/parada_tecnica/E2_PREREGISTRO_ENTORNO.md')}`)"
        f" → v2 (pre-registro `{_commit('docs/parada_tecnica/E2_PREREGISTRO_v2.md')}`, "
        "E2_RESPUESTA): Ω niega solo con evidencia de sesgo (LCB), U basada en la acción (U(Si, "
        "A) con Laplace) y evaluación acumulada en la capa. Las dos corridas quedan lado a lado.",
        ""]


def seccion_2a(base) -> list[str]:
    p2a = _j(base, "v2/p2a.json")
    co = _j(base, "v2/p2a_cooperacion_a9.json")["resultado"]
    ops = p2a["operaciones"]
    col, coop_v1 = ops["colaboracion_A_B"], ops["cooperacion_B_C"]
    t = p2a["seguimiento"]["T*"]
    pl = t["planificador_del_receptor"]
    ag = p2a["agentes"]
    contra = [o for k, o in ops.items() if k.startswith("contraejemplo")]
    return [
        "## Punto 2a · Cooperación, colaboración y transferencia a un agente novato", "",
        "- **Qué se demuestra (mecanismo):** la colaboración de un agente en un estado superior a "
        "uno inferior (Alg. 4.10, p. 116) y la cooperación entre pares del mismo estado (Alg. "
        "4.9, p. 109), con los axiomas de §4.3.1 (pp. 69–70), el invariante ΣP = K y la "
        "procedencia PROV-O (`prov:wasDerivedFrom`).",
        f"- **Comandos:** {S}p2a_compartir.py` y {S}p2a_cooperacion_a9.py`.",
        f"- **Números clave:** colaboración A ({ag['A']['estado']}) → B ({ag['B']['estado']}): "
        f"{'aceptada' if col['aceptada'] else 'rechazada'}, {col['conteo']['igual']} iguales, "
        f"{col['conteo']['similar']} similares, {col['conteo']['nueva']} nuevas. Cooperación B ↔ C "
        f"(los dos Novice) con A9 en decisiones: {'aceptada' if co['aceptada'] else 'rechazada'} "
        f"({co['conteo']['igual']}/{co['conteo']['similar']}/{co['conteo']['nueva']} de B en C y "
        f"{co['conteo_sentido_C_en_B']['igual']}/{co['conteo_sentido_C_en_B']['similar']}/"
        f"{co['conteo_sentido_C_en_B']['nueva']} de C en B); base común a los dos: "
        f"{'sí' if co['base_comun_a_los_dos'] else 'no'}; ΣP = K en los dos: "
        f"{'sí' if co['invariante_receptor'] and co['invariante_donante'] else 'no'}. "
        f"Contraejemplos rechazados por los axiomas: {sum(not o['aceptada'] for o in contra)} "
        f"de {len(contra)}.",
        f"- **La teoría fallida también sirve:** T* (Si: {_si(t['si'])}; A = {t['a']}; Sf: "
        f"calificado = {t['sf']['calificado']}) llega a B con P {t['en_receptor']['p']}, K "
        f"{t['en_receptor']['k']}, U {num(t['en_receptor']['u'], 3)}; en esa celda el planificador "
        f"de B elige {pl['accion']} (T{pl['teoria']}), no T*: la experiencia de fracaso que "
        "transfiere A evita que el novato repita el error.",
        "- **Archivos:** `docs/parada_tecnica/v2/p2a_compartir.md`, "
        "`docs/parada_tecnica/v2/p2a_procedencia.ttl`, "
        "`docs/parada_tecnica/E3_cooperacion_A9_lado_a_lado.md`.",
        *_rotulos(),
        f"- **Resultados inesperados:** con A9 en ventanas la cooperación B ↔ C se rechazó "
        f"({coop_v1['motivo']}).",
        f"- **Historial:** A9 en ventanas (E3) → A9 en decisiones (pre-registro corto "
        f"`{_commit('docs/parada_tecnica/E3_PREREGISTRO_A9.md')}`, E3_RESPUESTA): al menos 20 "
        "decisiones propias y los dos grupos. Motivo: con el gate por LCB la cantidad de "
        "decisiones ya entra en la cota; en el LLC se coopera entre SAR recién nacidos (p. 124).",
        ""]


def seccion_2b(base) -> list[str]:
    p2b = _j(base, "v2/p2b.json")
    p1 = _j(base, "v2/p1.json")
    ci, cii, ciii = (p2b["caso_i_misma_si"], p2b["caso_ii_si_nueva_con_similitud"],
                     p2b["caso_iii_sin_nada_aplicable"])
    cand = "; ".join(f"{c['puesto']}. T{c['id']} {c['a']} (U {num(c['u_tarea'], 3)}, P {c['p']}, "
                     f"K {c['k']})" for c in ci["alpha_1"]["candidatas"])
    n_des = p1["desacuerdos_fig421_alg47"]["veces"]
    n_des_v1 = _j(base, "v1/p1.json")["desacuerdos_fig421_alg47"]["veces"]
    return [
        "## Punto 2b · Ranking y recuperación de la teoría propia", "",
        "- **Qué se demuestra (mecanismo):** el planificador del LLC ordena las teorías de la celda "
        "por U desc, P desc y K asc (Fig. 4.21, p. 107) y la primera, si es un plan válido, decide "
        "la acción; sin teoría aplicable recurre al «azar» (Fig. 4.17, pp. 101–102), que acá es "
        "probar la acción todavía no probada o el operador BIO (DE-3).",
        f"- **Comando:** {S}p2b_planificador.py --version v2`.",
        f"- **Números clave:** (i) misma Si que T*: candidatas {cand}; elige "
        f"{ci['alpha_1']['accion']} ({ci['alpha_1']['motivo']}). (ii) Si nueva con similitud "
        f"máxima {num(cii['similitud_maxima'], 2)}: con respaldo por similitud, "
        f"{cii['con_respaldo']['accion']} ({cii['con_respaldo']['motivo']}); sin respaldo, "
        f"{cii['sin_respaldo_como_en_p1']['accion']} ({cii['sin_respaldo_como_en_p1']['motivo']}). "
        f"(iii) nada aplicable: {ciii['en_la_capa_del_agente']['accion']} "
        f"({ciii['en_la_capa_del_agente']['motivo']}).",
        "- **Archivos:** `docs/parada_tecnica/v2/p2b_planificador.md`.",
        *_rotulos(),
        f"- **Resultados inesperados:** la Fig. 4.21 y el Alg. 4.7 (p. 108) eligieron teorías "
        f"distintas {n_des} veces en P1 v2 y {n_des_v1} en P1 v1 (se informa para la decisión 2).",
        "- **Historial:** el mismo de P1 (v1 → v2).", ""]


def seccion_3(base) -> list[str]:
    d, desc = _j(base, "p3_equipos.json"), _j(base, "p3_descriptivas.json")
    m, fn = d["metricas"], desc["frente_al_neutro"]
    filas = []
    for r in ("parser", "matcher", "explainer"):
        def c(e, a):
            return next((p["ciclo"] for p in m[e][r]["promociones"] if p["a"] == a), "—")
        filas.append(f"| {TITULO[r]} | " + " | ".join(f"{c('B', a)} · {c('B0', a)}"
                                                    for a in ("Novice", "Trained", "Mature"))
                     + f" | {m['B'][r]['ciclos_exitosos']} · {m['B0'][r]['ciclos_exitosos']} |")
    rc = desc["regla_en_cada_ciclo"]

    def sost(e, r):
        return next((f["cumple_sin_interrupcion_desde"] for f in rc[e][r] if f["capa"] == "BIO"),
                    None)
    l3b = {r: d["l3"][r]["evaluadas"]["B"] for r in d["l3"]}
    iguales = [r for r, x in l3b.items()
               if d["l3"][r]["teorias_nuevas"]["B"] == 0 and x["pct_tna"] == x["pct_rtn"]]
    return [
        "## Punto 3 · Equipos DAG: un equipo maduro hace madurar a otro", "",
        "- **Qué se demuestra (mecanismo):** equipos DAG orquestados con LangGraph (Parser → "
        "Semantic Matcher → Bias Auditor → Orchestrator → Explainer); el equipo A colabora rol "
        "por rol con el equipo B al nacer; B0 es el control con los mismos casos; BC coopera con "
        "C en Novice; N es el SAR neutro de L-3.",
        f"- **Comandos:** {S}p3_equipos_dag.py` y {S}p3_descriptivas.py`.",
        "- **Números clave:** ciclo en que cada rol gana su estado, B · B0 (en los roles por "
        "caso, casos procesados), y ciclos exitosos B · B0:", "",
        "| Rol | Novice | Trained | Mature | Ciclos exitosos |", "|---|---|---|---|---|",
        *filas, "",
        f"  Casos resueltos de punta a punta: B {fn['B']['equipo']['aciertos']}, B0 "
        f"{fn['B0']['equipo']['aciertos']}, neutro {fn['N']['equipo']} (de {fn['casos']}). En BIO, la "
        f"regla se cumple sin interrupción desde el ciclo {sost('B', 'parser')} en el Parser de B "
        f"({sost('B0', 'parser')} en B0) y {sost('B', 'explainer')} en el Explainer "
        f"({sost('B0', 'explainer')} en B0). L-3 literal entre configuraciones (B evaluada): "
        + "; ".join(f"{TITULO[r]} %CEA {num(x['pct_cea'], 1)} ≥ %RCE {num(x['pct_rce'], 1)}, "
                    f"%TNA {num(x['pct_tna'], 1)} ≤ %RTN {num(x['pct_rtn'], 1)}: "
                    f"{'evoluciona' if x['evoluciona'] else 'no evoluciona'}"
                    for r, x in l3b.items()) + ".",
        "- **Nota técnica sobre L-3, para conversar con Jorge.** Con estas definiciones, %TNA ≤ "
        "%RTN equivale a «promedio de teorías nuevas ≤ máximo», y %CEA ≥ %RCE, a «ciclos exitosos "
        "de la configuración evaluada ≥ promedio de las configuraciones». "
        + (" y ".join(TITULO[r] for r in iguales) + ": %TNA = %RTN porque B no generó teorías "
           "propias (las recibió todas de A); la condición se cumple por igualdad. "
           if iguales else "")
        + f"El %CEA del Explainer ({num(l3b['explainer']['pct_cea'], 1)}) es tan alto porque el "
        f"operador BIO neutro casi nunca completa la explicación: el Explainer de N tuvo "
        f"{d['l3']['explainer']['ciclos_exitosos']['N']} ciclos exitosos de {fn['casos']}.",
        f"- **Cuánto pesa el entorno.** Las magnitudes dependen del entorno pre-registrado: los "
        f"operadores BIO son imperfectos por construcción, y el equipo neutro resuelve "
        f"{fn['N']['equipo']} de {fn['casos']} casos. Los resultados muestran el mecanismo de "
        "colaboración y maduración, no cuánto ayudaría en un sistema real.",
        "- **Figuras:** `docs/parada_tecnica/p3_maduracion_equipos.png`, "
        "`docs/parada_tecnica/p3_curvas_aprendizaje.png`.",
        *_rotulos(),
        "- **Resultados inesperados:** el Matcher de B gana Novice y Trained más tarde que el de "
        "B0 (su Parser, con las teorías de A, sube el punto de comparación), pero solo él llega a "
        "Mature; Parser y Explainer promueven en el primer cierre posible en todos los equipos "
        "(piso de 20 ciclos por estado); el Matcher de C no sale de Born, así que no coopera "
        "(axioma [a]); la semilla de E4 es poco frecuente (`e4_muestreo_calificados.md`).",
        "- **Historial:** desde E5, por E4_RESPUESTA: el Bias Auditor no tiene estados ganados, "
        "solo el Explainer explora en WIO y la Si del Explainer es tipo · destinatario. Las "
        "métricas descriptivas (frente al neutro y curvas sin piso) se agregaron por E5_RESPUESTA "
        "sobre las mismas corridas.", ""]


def seccion_4(base) -> list[str]:
    d = _j(base, "p4_equipo.json")
    sh = d["shacl"]
    roles = d["equipo"]["roles"]
    exp = d["celdas_sin_exito_en_wio"]["explainer"]
    return [
        "## Punto 4 · La traza de cada etapa de cada rol", "",
        "- **Qué se demuestra (mecanismo):** para cada rol del equipo y cada caso, la situación "
        "inicial, las candidatas y la acción, la situación final, P, K y U, la región en que se "
        "registró la teoría y el estado del agente; todo en RDF con PROV-O, verificado con SHACL "
        "(ΣP = K, DE-4) y consultable con SPARQL.",
        f"- **Comando:** {S}p4_traza.py`.",
        f"- **Números clave:** {sh['tripletas']} tripletas ("
        + ", ".join(f"{k} {v}" for k, v in sh["clases"].items()) + "); SHACL conforma: "
        f"{'sí' if sh['conforma'] else 'no'}; las dos pruebas negativas fallan como deben: "
        f"{'sí' if sh['negativa_sigma_p'] and sh['negativa_de4'] else 'no'}. Estados ganados: "
        + ", ".join(f"{TITULO[r]} {x['estado']}" for r, x in roles.items()
                    if r != "bias_auditor")
        + f"; Bias Auditor: {roles['bias_auditor']['estado']} en E4; desde E5 no tiene estados por "
        "diseño (su regla es regulatoria; decisión 1 de E4_RESPUESTA).",
        "- **Archivos:** " + ", ".join(f"`docs/parada_tecnica/{t}`" for t in d["trazas"]
                                       if t.endswith(".html"))
        + ", `docs/parada_tecnica/p4_equipo.ttl`, `p4_shacl.txt`, `p4_sparql.md`.",
        *_rotulos(),
        "- **Resultados inesperados:** el contrafáctico CE_0 se corrigió antes de la corrida "
        "oficial (Parser y Explainer); el Explainer llegó a Mature con una celda que nunca "
        f"resolvió ({exp[0]['ciclos'] if exp else 0} fracasos en WIO), lo que motivó la decisión 3 "
        "de E4_RESPUESTA; el Bias Auditor no puede promover con la regla de P1 (su acción la decide "
        "la regla).",
        "- **Historial:** E4 queda como está; las reglas de E5 valen desde E5.", ""]


def seccion_5(base) -> list[str]:
    c1, c2 = _j(base, "p5_metricas_equidad.json"), _j(base, "p5_sesgo_programado.json")
    v2, ctl = _j(base, "p5_equidad_v2.json"), _j(base, "p5_control_post_hoc.json")
    a1, a5, r2 = c1["alpha_1.0"]["roles"], c1["alpha_0.5"]["roles"], v2["corrida_1"]["roles"]
    p2 = a1["matcher"]["primeros_260"]
    det = c2["detectable"]["configuraciones"]
    der = det["neutro"]["ventanas_derivadas_regla_acumulada"]
    t1 = {k: sum(a5[r]["alpha_0_5"][k] for r in ("parser", "matcher", "explainer"))
          for k in ("eleccion_cambiada", "accion_cambiada")}
    t2 = {k: sum(r2[r]["alpha_0_5"][k] for r in ("parser", "matcher", "explainer"))
          for k in ("eleccion_cambiada", "accion_cambiada")}
    aj = {k: sum(r2[r]["ajuste_v2"][k] for r in ("parser", "matcher", "explainer"))
          for k in ("aplicado", "no_aplicable_falta_evidencia")}
    k = ctl["control"]
    return [
        "## Punto 5 · Métricas de equidad en la utilidad de cada rol", "",
        "- **Qué se demuestra (mecanismo):** una métrica de equidad por rol, calculada en el plano "
        "de auditoría (el grupo nunca entra en Si, A ni los prompts); U_rol = α·U + (1 − α)·ê en "
        "la utilidad; y, con un sesgo programado por un proxy, cuándo las reglas del Monitor de "
        "Equidad pueden actuar y cuándo no. Documento para la dirección: "
        "`docs/parada_tecnica/METRICAS_EQUIDAD_POR_ROL.md`.",
        f"- **Comandos:** {S}p5_metricas_equidad.py`, {S}p5_equidad_v2.py`, "
        f"{S}p5_control_post_hoc.py` y {S}metricas_equidad_doc.py`.",
        f"- **Números clave:** en los 600 casos, Parser brecha de completitud "
        f"{_n(a1['parser']['favorable']['brecha'])} (d_TV del canal proxy "
        f"{_n(a1['parser']['dtv_canal_proxy'])}); Matcher odds igualadas "
        f"{_n(a1['matcher']['odds_igualadas']['eo'])} y paridad demográfica "
        f"{_n(a1['matcher']['favorable']['brecha'])} (diferencia de calificados "
        f"{_n(c1['calificados_del_flujo']['brecha'])}); Explainer "
        f"{_n(a1['explainer']['favorable']['brecha'])}; Bias Auditor Δ_esc "
        f"{_n(a1['bias_auditor']['favorable']['brecha'])}. Tres criterios que no coinciden (casos "
        f"de E4): paridad demográfica {_n(p2['paridad_demografica']['brecha'])}, aciertos "
        f"{_n(p2['aciertos_por_grupo']['tasas']['AR'])} y "
        f"{_n(p2['aciertos_por_grupo']['tasas']['no-AR'])}, TPR "
        f"{_n(p2['odds_igualadas']['tpr']['AR'])} y {_n(p2['odds_igualadas']['tpr']['no-AR'])}.",
        f"- **U_rol con α = 0,5:** v1 (ê por teoría) cambió la teoría {t1['eleccion_cambiada']} "
        f"veces y la acción {t1['accion_cambiada']}; v2 (ê por celda) se aplicó en {aj['aplicado']} "
        f"planificaciones, no se pudo aplicar por falta de evidencia en "
        f"{aj['no_aplicable_falta_evidencia']}, y cambió la teoría {t2['eleccion_cambiada']} y la "
        f"acción {t2['accion_cambiada']} veces.",
        f"- **Sesgo programado** («parámetros programados»; brecha del operador "
        f"{num(c2['detectable']['brecha_operador_esperada'], 2)}): la regla de ventana de 20 no "
        f"deriva nunca; la regla acumulada deriva al neutro desde {der[0] if der else '—'} "
        f"({len(der)} ventanas); el Matcher que aprende baja la paridad demográfica de "
        f"{_n(det['neutro']['brecha_toda_la_corrida'])} a {_n(det['alpha_1']['brecha_toda_la_corrida'])}"
        " y ninguna regla lo detecta; Ω acepta su compartición. Atenuación: ilustra el "
        "mecanismo; no es evidencia de la conjetura de atenuación.",
        "- **Qué significa que α = 0,5 no haya cambiado nada.** El ajuste funciona: el test "
        "`tests/test_bloquee_e6_v2.py::test_la_equidad_por_celda_puede_cambiar_la_accion` muestra "
        "que, con evidencia en las dos acciones y U parecidas, α = 0,5 cambia la acción. El ajuste "
        "por equidad necesita evidencia sobre la acción que el agente no elige, y el aprendizaje "
        f"deja de generarla (en {aj['no_aplicable_falta_evidencia']} de "
        f"{aj['aplicado'] + aj['no_aplicable_falta_evidencia']} planificaciones faltó evidencia). "
        "Es una propiedad del tamaño de muestra y de la explotación, no de la definición.",
        f"- **Control post hoc** («{ctl['rotulo']}»): Matcher sin rasgo ni sesgo, paridad "
        f"demográfica {_n(k['brecha_toda_la_corrida'])}, odds igualadas "
        f"{_n(k['odds_igualadas']['eo'])}, estado final {k['estado_final']}. La diferencia con el "
        f"Matcher sesgado que aprende ({_n(det['alpha_1']['brecha_toda_la_corrida'])} frente a "
        f"{_n(k['brecha_toda_la_corrida'])}) da una idea del sesgo residual atribuible al proxy, "
        f"del orden de {_n(ctl['frente_al_matcher_sesgado_que_aprende']['detectable']['paridad_demografica']['diferencia'], 2)}"
        ", con la salvedad de que el control no es un contrafáctico limpio: llegó a Mature y no "
        "explora en WIO.",
        "- **Figura:** `docs/parada_tecnica/p5_sesgo_programado.png`.",
        *_rotulos(),
        "- **Resultados inesperados:** α = 0,5 no cambió ninguna acción ni en la v1 ni en la v2; "
        "paridad de aciertos pareja no implica odds igualadas; el gate de compartición dejó pasar "
        "al Matcher sesgado (la brecha estaba por debajo de lo detectable); ê casi no ve el sesgo "
        "por proxy (pocas lecturas de AR en las celdas sin título local).",
        f"- **Historial:** E6 (pre-registro `{_commit('docs/parada_tecnica/E6_PREREGISTRO.md')}`, ê "
        f"por teoría) → E6 v2 (pre-registro corto "
        f"`{_commit('docs/parada_tecnica/E6_PREREGISTRO_v2.md')}`, E6_RESPUESTA): ê por celda (Si, "
        "A), y sin evidencia en alguna candidata α = 1 para todas. Motivo: con U(Si, A) la v1 solo "
        "reordenaba variantes de la misma acción y su respaldo premiaba la falta de evidencia.", ""]


PREGUNTAS = [
    ("Decisión 1 de la hoja", "¿La evolución y la compartición se condicionan a la ausencia de "
     "evidencia de sesgo (lo implementado: LCB > τ_b niega) o a la evidencia de equidad?"),
    ("A9", "¿La historia mínima para donar (extensión nuestra, no del LLC) se mide en decisiones "
     "(lo implementado desde E3) o en ventanas?"),
    ("Ω sin ciclo de vida", "¿El Monitor de Equidad debe tener un ciclo de vida propio? La "
     "propuesta es que no: su regla es regulatoria (BIO) y no se aprende."),
    ("Con qué se compara un agente dentro de un equipo", "¿Contra sus propias entradas (lo que "
     "aprendió él; lo implementado para la promoción) o contra el equipo neutro (su aporte al "
     "resultado conjunto)?"),
    ("Criterio del rol decisor", "¿Qué criterio de equidad fija la dirección para el Matcher? "
     "La propuesta es odds igualadas a nivel rol."),
    ("Sesgo por proxy por debajo de lo detectable", "¿Reportar el d_TV como alerta, exigir más "
     "historia antes de compartir o aceptar el límite?"),
    ("Observación selectiva en WIO", "En WIO la Sf la da la revisión humana de todos los casos; "
     "en producción solo se observa el resultado de los que avanzan. ¿Se modela?"),
    ("Si, A y Sf por rol", "¿Se aceptan las definiciones de la sección 6 del handoff tal como "
     "quedaron corridas (con la Si del Explainer sin «motivos» desde E5)?"),
    ("%RCE, %RTN, n y α", "¿Se aceptan los valores fijados antes de correr ({valores})? En la "
     "tesis, los porcentajes se determinan comparando configuraciones de SAR (Anexo L-3, Tablas "
     "L-16 y L-17)."),
    ("Semántica LLC de P y K (decisión 2)", "¿Se adopta el registro de la Fig. 4.13 con ΣP = K "
     "(implementado como opción) frente a la semántica anterior?"),
    ("Similitud como extensión del planificador", "¿Se acepta el respaldo por similitud (solo con "
     "la celda vacía, registrado) como extensión declarada para situaciones en lenguaje natural?"),
    ("Equidad en la utilidad con poca evidencia", "Con m_min = {m_min} lecturas por grupo, el "
     "ajuste casi nunca se aplica, porque el agente deja de probar la acción que no elige. ¿Se "
     "exige exploración mínima para estimar la equidad de ambas acciones, se baja m_min o se "
     "acepta el límite?"),
]


def escribir(out=None) -> str:
    base = out_dir(out)
    L = encabezado_md("Parada técnica: la prueba de concepto como ciclo de vida (Bloque E)")
    L += ["Informe para la dirección (Jorge Ierache y Martín Becerra). Selección de personal es "
          "el dominio de experimentación. Todas las cifras salen de correr el código en el modo "
          "sim; cada sección dice cómo reproducirla. Para regenerar todo y comparar byte a byte "
          f"con lo commiteado: {S}generar_todo.py --verificar`.", "",
          "Pedido de la dirección: (1) correr un caso que genere una teoría y mostrar punto a "
          "punto el ciclo de vida; (2a) cooperación, colaboración y transferencia a un agente "
          "novato; (2b) ranking y recuperación de la teoría propia; (3) equipos DAG que maduran a "
          "otro equipo; (4) la traza de cada etapa de cada rol; (5) las métricas de equidad en la "
          "utilidad de cada rol.", ""]
    for f in (seccion_1, seccion_2a, seccion_2b, seccion_3, seccion_4, seccion_5):
        L += f(base)
    L += ["## Preguntas para el encuentro", ""]
    cfg = cargar_config()
    cv = cfg["ciclo_de_vida"]
    valores = (f"%RCE {cv['rce']}, %RTN {cv['rtn']}, intervalos de {cv['n_intervalo']} ciclos, "
               "α = " + " y ".join(num(a, 1) for a in cfg["equipo_e6"]["equipo_equidad"]["alphas"]))
    L += [f"{i}. **{t}.** {q.format(valores=valores, m_min=cfg['utilidad']['m_min_por_grupo'])}"
          for i, (t, q) in enumerate(PREGUNTAS, 1)]
    L += ["", "## Estado", "",
          "Rama `eje1/bloque-e`, revisada por Claude chat "
          "(`docs/parada_tecnica/E7_REVISION_ClaudeChat_2026-10-08.md`); sin merge a `main`, que "
          "queda congelada hasta después del encuentro con la dirección. Los puntos de control de "
          "cada fase y las respuestas de Claude chat están en `docs/parada_tecnica/` (E0 a E7). No "
          "se adoptó ninguna de las decisiones de la hoja: están implementadas como opciones para "
          "que la dirección las evalúe funcionando.", "",
          "**Infraestructura.** La orquestación con LangGraph existió desde la primera versión "
          "(06/06/2026) y quedó fuera del historial al reorganizarlo; E1 la restituye "
          "(`core/grafo.py`); el código de junio queda en la rama `rescate/langgraph-junio`.", ""]
    (base / "INFORME_PARADA_TECNICA.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    p4 = _j(base, "p4_equipo.json")
    traza = next(t for t in p4["trazas"] if t.endswith(".html") and "TBO" in t)
    M = encabezado_md("Guion para mostrar en vivo (10 pasos)")
    M += [f"1. Verificar que todo se regenera igual: {S}generar_todo.py --verificar` (unos minutos).",
          "2. Abrir `docs/parada_tecnica/INFORME_PARADA_TECNICA.md`: una sección por punto del "
          "pedido.",
          f"3. Punto 1: {S}p1_teoria_punto_a_punto.py --version v2 --out /tmp/demo` y abrir "
          "`docs/parada_tecnica/v2/p1_traza_ciclo1.md` (las siete regiones del primer ciclo).",
          "4. Punto 1: figura `docs/parada_tecnica/v2/p1_linea_de_tiempo.png` (Born → Mature).",
          "5. Punto 2b: `docs/parada_tecnica/v2/p2b_planificador.md` (orden de la Fig. 4.21 y "
          "«azar»).",
          "6. Punto 2a: `docs/parada_tecnica/v2/p2a_compartir.md` (colaboración, cooperación, "
          "axiomas y la teoría fallida que evita el error).",
          f"7. Punto 4: abrir `docs/parada_tecnica/{traza}` en el navegador (una tabla por rol).",
          "8. Punto 3: figuras `docs/parada_tecnica/p3_maduracion_equipos.png` y "
          "`docs/parada_tecnica/p3_curvas_aprendizaje.png`.",
          "9. Punto 5: figura `docs/parada_tecnica/p5_sesgo_programado.png` y "
          "`docs/parada_tecnica/METRICAS_EQUIDAD_POR_ROL.md`.",
          "10. Cerrar con «Preguntas para el encuentro» al final del informe.", ""]
    (base / "LEEME_REUNION.md").write_text("\n".join(M) + "\n", encoding="utf-8")
    return str(base / "INFORME_PARADA_TECNICA.md")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None)
    print(escribir(ap.parse_args().out))
