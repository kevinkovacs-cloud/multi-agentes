#!/usr/bin/env python
"""
Informe del punto de control de E4 (Bloque E, punto 4 del pedido): escribe
docs/parada_tecnica/E4_PUNTO_DE_CONTROL.md desde las salidas de P4 (p4_equipo.json), de P1 v2
(v2/p1.json) y de las reglas pre-registradas del entorno. Ningún número a mano.

Uso:  python experiments/parada_tecnica/informe_e4.py [--out DIR] [--correr]
"""
from __future__ import annotations
import argparse
import json
import subprocess

from comun_pt import REPO, cargar_config, encabezado_md, num, out_dir
from moav_hr.instances.hr import entorno

ROL = {"parser": "Parser", "matcher": "Semantic Matcher", "bias_auditor": "Bias Auditor",
       "explainer": "Explainer"}


def _commit(ruta: str) -> str:
    """Primer commit que agregó el archivo (para citar el pre-registro sin escribirlo a mano)."""
    r = subprocess.run(["git", "log", "--diff-filter=A", "--format=%h", "--", ruta], cwd=REPO,
                       capture_output=True, text=True)
    return (r.stdout.strip().splitlines() or ["(sin commit)"])[-1]


def _promos(info: dict) -> str:
    return "; ".join(f"ciclo {p['ciclo']}: {p['de']} → {p['a']}" for p in info["promociones"]) \
        or "ninguna"


def _si(si: dict) -> str:
    return " · ".join(str(v) for v in si.values())


def escribir(out=None) -> str:
    base = out_dir(out)
    d = json.loads((base / "p4_equipo.json").read_text(encoding="utf-8"))
    p1 = json.loads((base / "v2" / "p1.json").read_text(encoding="utf-8"))
    cfg = cargar_config()
    om, cv = cfg["omega"], cfg["ciclo_de_vida"]
    pre = entorno.describir_entorno_e4(om["tau_b"], om["delta"], cfg["equipo_e4"]["ventana"])
    roles, ev, mot = d["equipo"]["roles"], d["evaluaciones"], d["motivos_por_capa"]
    sh, br = d["shacl"], d["sparql"]["brecha_por_rol"]
    ac = d["analisis_cadena"]
    L = encabezado_md("E4 · Punto de control del Bloque E (punto 4 del pedido)")
    L += ["Rama `eje1/bloque-e`, sin push. Pre-registro de E4 commiteado antes de correr P4 "
          f"(`{_commit('docs/parada_tecnica/E4_PREREGISTRO.md')}`, "
          "`docs/parada_tecnica/E4_PREREGISTRO.md`): reglas 7 a 10 del entorno, estrategias de "
          "cada rol y sección `equipo_e4` de la config. Ningún parámetro se cambió después de "
          "correr.", "",
          "## Qué se hizo", "",
          "- **Teorías y ciclo de vida para todos los roles** (sección 6 del handoff). Parser: Si "
          "= plantilla del documento; A = reglas estrictas (operador BIO) o diccionario de "
          "sinónimos; Sf = completitud y fuga validadas por un shape SHACL del perfil. Bias "
          "Auditor (DE-6): un ciclo por ventana; la acción la decide la regla certificada; Sf = "
          "revisión de la ventana. Explainer: Si = tipo, destinatario y motivos; A = por "
          "factores (operador BIO), contrafáctica o regulatoria; Sf = completitud verificada "
          "por SPARQL contra el grafo RDF del caso. El Orchestrator no tiene teorías (DE-7).",
          "- **Equipo DAG orquestado con LangGraph** (`instances/hr/equipo_llc.py`, "
          "`core/grafo.py`): Parser → Semantic Matcher → Bias Auditor → Orchestrator → "
          f"Explainer, un StateGraph por ventana; {d['equipo']['casos']} casos en "
          f"{d['equipo']['ventanas']} ventanas. Cada rol transita su propia capa con su propio "
          "ciclo de vida (`MotorLLC.paso`); los estados se ganan, ninguno se fija a mano.",
          f"- **ABox** (`core/ontology/abox_llc.py`, `p4_equipo.ttl`): {sh['tripletas']} "
          "tripletas; " + ", ".join(f"{k} {v}" for k, v in sh["clases"].items()) + ". Cada "
          "teoría con `prov:wasGeneratedBy` el ciclo en que nació (región 5), su rol y su "
          "agente; siete nodos de región por ciclo con sus valores; decisiones informadas por "
          "los ciclos de cada rol; lecturas de equidad en el plano de auditoría.",
          f"- **SHACL** (`core/ontology/shapes_llc.py`, `p4_shacl.txt`): conforma "
          f"**{'sí' if sh['conforma'] else 'no'}**. ΣP = K por celda (Si, A) como restricción "
          "SPARQL (Fig. 4.13, p. 113) y DE-4 sobre la región 1. Las dos pruebas negativas "
          f"(P + 1 en una teoría; un atributo protegido en una región 1) "
          f"{'fallan, como deben' if sh['negativa_sigma_p'] and sh['negativa_de4'] else 'NO fallan'}.",
          "- **SPARQL** (`core/ontology/queries_llc.py`, `p4_sparql.md`): genealogía de una "
          "teoría, qué teorías de qué roles intervinieron en una decisión, teorías por rol y "
          "estado, resultado favorable por rol y grupo.",
          "- **Trazas legibles para la reunión:** " + ", ".join(
              f"`{t}`" for t in d["trazas"]) + ".", "",
          "## Resultados", "",
          "| Rol | Estado final | Promociones | Ciclos | Teorías | Evaluaciones de R7 |",
          "|---|---|---|---|---|---|"]
    for r, info in roles.items():
        L.append(f"| {ROL[r]} | {info['estado']} | {_promos(info)} | {info['ciclos']} | "
                 f"{info['teorias']} | {info['evaluaciones']} |")
    L += ["", "**Motivo de cada acción, por capa del rol** (celda = plan de una teoría; azar = "
          "exploración o operador BIO, DE-3; regla = la regla certificada, DE-6):", "",
          "| Rol | Capa | Motivos |", "|---|---|---|"]
    for r, capas in mot.items():
        for capa, m in capas.items():
            L.append(f"| {ROL[r]} | {capa} | " + ", ".join(f"{k} {v}" for k, v in m.items())
                     + " |")
    L += ["", "**Resultado favorable por rol y grupo** (consulta 4 de `p4_sparql.md`):", "",
          "| Rol | Tasa AR | Tasa no-AR | Brecha |", "|---|---|---|---|"]
    for r, b in br.items():
        L.append(f"| {ROL[r]} | {num(b['tasas']['AR'], 3)} | {num(b['tasas']['no-AR'], 3)} | "
                 f"{num(b['brecha'], 3)} |")
    ventanas = d["ventanas"]
    alta = [v["id"] for v in ventanas if v["sf"]["brecha_errores"] == "alta"]
    L += ["", f"**Bias Auditor:** {len(ventanas)} ventanas, todas "
          f"{'LIBERAR' if all(v['accion'] == 'LIBERAR' for v in ventanas) else 'con alguna DERIVAR'}; "
          f"brecha de paridad observada máxima {num(max(v['brecha_dp'] for v in ventanas), 3)}, "
          f"LCB máxima {num(max(v['lcb'] for v in ventanas), 3)} (τ_b = {num(om['tau_b'], 3)}). "
          f"Decisiones finales: " + ", ".join(f"{k} {v}" for k, v in
                                               d["decisiones_finales"].items()) + ".", "",
          "## Resultados que no fueron los esperados", ""]
    exp_celdas = d["celdas_sin_exito_en_wio"]["explainer"]
    n_exp_wio = sum(mot["explainer"].get("WIO", {}).values())
    L += ["1. **CE_0 del SAR neutro, corregido antes de la corrida oficial.** En la primera "
          "prueba del equipo (sin salidas commiteadas) Parser y Explainer daban CE_a = CE_0 en "
          "todas las evaluaciones: el motor calculaba el acierto del operador BIO con la Sf de la "
          "acción del agente. Para el Matcher es correcto (la verdad no depende de la acción); "
          "para Parser y Explainer, no (la Sf depende de la estrategia). Corrección: el rol da "
          "la Sf contrafáctica del operador BIO sobre el mismo caso (`sf_contrafactica`). Es la "
          "definición pre-registrada de CE_0 («contrafáctico determinista del simulador»), no un "
          "cambio de regla; P1, P2b y P2a dan la misma salida."]
    if exp_celdas:
        c = exp_celdas[0]
        ap = c["apariciones_por_capa"]
        antes = c["acciones_probadas_antes_de_WIO"]
        nunca = [a for a in entorno.ESTRATEGIAS_EXPLAINER if a not in antes]
        L += [f"2. **El Explainer llega a Mature con una celda que nunca resuelve.** En la celda "
              f"«{_si(c['si'])}» falló en los {c['ciclos']} ciclos que tuvo en WIO (de "
              f"{n_exp_wio} ciclos del rol en WIO), siempre con su operador BIO (motivos: "
              + ", ".join(f"{k} {v}" for k, v in c["motivos"].items()) + "). Antes de WIO la "
              f"celda apareció {ap['BIO'] + ap['TBO']} veces (BIO {ap['BIO']}, TBO {ap['TBO']}) "
              f"y el rol probó {', '.join(antes) or 'ninguna estrategia'}; "
              f"{', '.join(nunca)} no se probó nunca. Mecanismo: (a) en WIO no hay exploración "
              "(decisión P3 aprobada: «azar» solo en BIO y TBO); (b) la celda aparece sobre "
              "todo cuando el Matcher ya decide con teorías (motivos = varios), y para entonces "
              "el Explainer ya está en WIO; (c) la regla de evolución mira el agregado de ciclos "
              "exitosos, no la cobertura de celdas. El Matcher tiene el mismo efecto en "
              f"{len(d['celdas_sin_exito_en_wio']['matcher'])} celdas chicas ("
              + ", ".join(str(x["ciclos"]) for x in d["celdas_sin_exito_en_wio"]["matcher"])
              + " ciclos en WIO). Se reporta tal cual; ver la pregunta 3."]
    pm = p1["resultado"]
    wio_m = [e for e in ev["matcher"] if e["capa"] == "WIO"]
    L += [f"3. **El Matcher del equipo termina en {roles['matcher']['estado']}**, mientras que en "
          f"P1 v2 llegó a {pm['estado_final']}. En el equipo percibe el perfil extraído y recorre "
          "otra secuencia de casos (su capa no coincide con el escenario). En WIO, su %CEA "
          "acumulado quedó en " + ", ".join(num(e["pct_cea"], 1) for e in wio_m)
          + f", siempre por debajo de %RCE = {cv['rce']}."]
    bio_gap = abs(pre["parser"]["por_grupo"]["AR"]["p_completo_operador_bio"]
                  - pre["parser"]["por_grupo"]["no-AR"]["p_completo_operador_bio"])
    cal = {g: sum(ac[e][g]["calificados"] * ac[e][g]["casos"] for e in ac)
           / sum(ac[e][g]["casos"] for e in ac) for g in ("AR", "no-AR")}
    aci = {g: sum(ac[e][g]["aciertos_matcher"] * ac[e][g]["casos"] for e in ac)
           / sum(ac[e][g]["casos"] for e in ac) for g in ("AR", "no-AR")}
    lcb_max = max((e["lcb"] or 0.0) for r in ev for e in ev[r])
    L += [f"4. **El efecto en cadena previsto casi no se ve.** El pre-registro preveía, con el "
          f"operador BIO del Parser, una brecha de completitud de {num(bio_gap, 3)} entre grupos "
          "(canal proxy declarado). El Parser aprendió la estrategia de cada plantilla en el "
          f"primer intervalo, y la brecha de completitud de toda la corrida fue "
          f"{num(br['parser']['brecha'], 3)}. En el escenario BIO, la completitud fue "
          f"{num(ac['BIO']['AR']['perfil_completo'], 3)} (AR) y "
          f"{num(ac['BIO']['no-AR']['perfil_completo'], 3)} (no-AR).",
          f"5. **La brecha de paridad del Matcher ({num(br['matcher']['brecha'], 3)}) sigue a la "
          "tasa de calificados del flujo de casos, no al Parser.** En los casos de esta corrida "
          f"los calificados son {num(cal['AR'], 3)} (AR) y {num(cal['no-AR'], 3)} (no-AR). Es "
          "una diferencia de muestreo: el grupo se asigna alternado e independiente de la Si y "
          "de la verdad. La paridad demográfica la cuenta como brecha aunque la tasa de aciertos "
          f"del Matcher sea parecida: {num(aci['AR'], 3)} (AR) y {num(aci['no-AR'], 3)} (no-AR) "
          "en toda la corrida (por escenario y grupo en `p4_equipo.json`, `analisis_cadena`). Es "
          "la tensión conocida entre paridad demográfica y paridad de errores. Ω no negó ninguna "
          f"promoción: la LCB más alta en las evaluaciones de todos los roles fue "
          f"{num(lcb_max, 3)}.",
          "6. **Bias Auditor, como estaba previsto:** queda en Born y nunca deriva. No puede "
          "promover (CE_a = CE_0) ni cerrar un intervalo de R7 "
          f"({len(ventanas)} ciclos < {cv['n_intervalo']}). Con ventanas de 20, la regla "
          f"certificada no puede derivar (LCB máxima posible {num(pre['auditor']['lcb_maxima'], 4)} "
          f"< τ_b). Aun así, sus teorías registran {len(alta)} ventanas con brecha de errores "
          "«alta» (" + ", ".join(alta) + "). Son las «teorías de sesgo» para auditoría: "
          "muestran lo que la regla certificada no puede ver con ventanas de este tamaño.",
          "7. **Parser y Explainer llegan a Mature en los primeros 60 ciclos de cada uno** "
          "(operador BIO débil frente a la mejor estrategia). Después siguen en servicio sin "
          "evaluar R7 (pre-registro E4).",
          "8. **Ajustes menores, sin efecto en números:** (a) el motor usaba un trail propio si "
          "el que recibía estaba vacío (`or` sobre un AuditTrail de longitud 0); en el equipo "
          "hace falta uno compartido, y ahora se usa `is None`. (b) `TeoriaLLCShape` exige al "
          "menos un `prov:wasGeneratedBy`, no exactamente uno, porque una teoría que llega por "
          "compartir tiene dos actividades: su ciclo de nacimiento y la de compartir. (c) Se "
          "regeneró `v2/p2a.json`: el commiteado era anterior a la clave `a9` (solo suma esa "
          "clave; ningún número cambia).", "",
          "## Preguntas para Claude chat (y, si corresponde, para la dirección)", "",
          "1. **Evolución del Bias Auditor.** Con DE-6 (la regla decide) y la regla de P1 "
          "(%CEA frente al SAR neutro), el Auditor no puede evolucionar nunca. Opciones: (a) "
          "dejarlo sin estados ganados, como el Orchestrator, y conservar sus teorías solo para "
          "auditoría; (b) un criterio propio de evolución (por ejemplo, u de sus intervenciones "
          "frente a la revisión), declarado como extensión; (c) dejarlo así y mostrarlo como "
          "límite.",
          "2. **Ventana del Auditor.** Con 20 casos la regla certificada no puede derivar. ¿Se "
          "mantiene (coherente con fair(W) de 20) o se usa una ventana más grande (por ejemplo, "
          "acumulada en la capa), sabiendo que habría menos ciclos del Auditor?",
          "3. **Exploración en WIO para roles que no deciden sobre personas** (Parser y "
          "Explainer). La decisión P3 («azar» solo en BIO y TBO) protege a las personas en el "
          "Matcher, pero deja trabado al Explainer (resultado 2). ¿Se permite probar una "
          "acción no probada en WIO para esos roles, o se exige cobertura de celdas antes de "
          "promover?",
          "4. **Regla del equipo:** cada rol transita su propia capa y el escenario solo fija "
          "los casos. ¿Se acepta para E5?",
          "5. **Canal proxy en las plantillas del Parser** (frecuencia por grupo declarada). ¿Se "
          "mantiene para E5 y E6, o se corre con plantillas independientes del grupo?",
          "6. **«Motivos» en la Si del Explainer.** Lo pide la sección 6, no cambia la mejor "
          "estrategia y parte celdas que aparecen tarde (resultado 2). ¿Se mantiene?", "",
          "## Qué sigue", "",
          "E5 (equipo maduro A, equipo B que recibe colaboración rol por rol, control B0 y "
          "cooperación), E6 (métricas de equidad por rol) y E7 (informe y cierre). **Frenado en "
          "el punto de control de E4.** Sin push.", ""]
    ruta = base / "E4_PUNTO_DE_CONTROL.md"
    ruta.write_text("\n".join(L) + "\n", encoding="utf-8")
    return str(ruta)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Informe del punto de control de E4")
    ap.add_argument("--out", default=None)
    ap.add_argument("--correr", action="store_true", help="corre P4 antes de escribir")
    a = ap.parse_args()
    if a.correr:
        import p4_traza
        p4_traza.correr(a.out)
    print(escribir(a.out))
