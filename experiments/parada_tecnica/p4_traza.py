#!/usr/bin/env python
"""
P4 · Todos los roles con su ciclo de vida y la traza completa (punto 4 del pedido; E4).

Un equipo DAG (Parser → Semantic Matcher → Bias Auditor → Orchestrator → Explainer,
orquestado con LangGraph) procesa el flujo de casos pre-registrado (sección `equipo_e4` de
configs/parada_tecnica.yaml; docs/parada_tecnica/E4_PREREGISTRO.md). Cada rol con teorías
recorre su propio ciclo de vida del LLC. Salidas en docs/parada_tecnica/:

  · p4_traza_<caso>.md y .html: para cada caso pre-registrado, una tabla por rol con la
    situación inicial, las candidatas y la acción, la situación final, P, K y U, la región
    en que se registró y el estado del agente;
  · p4_equipo.ttl (ABox del equipo), p4_shacl.txt (validación, con ΣP = K y dos pruebas
    negativas), p4_sparql.md (las cuatro consultas y sus resultados) y p4_equipo.json.

Uso:  python experiments/parada_tecnica/p4_traza.py [--out DIR]
"""
from __future__ import annotations
import argparse
import copy
import html
import json

from rdflib import Literal
from rdflib.namespace import RDF, XSD

from comun_pt import (ROTULOS, cargar_config, encabezado_md, guardar_json, mayus, num,
                      out_dir)
from moav_hr.core.ontology import queries_llc as Q
from moav_hr.core.ontology.abox import theory_iri
from moav_hr.core.ontology.abox_llc import abox_equipo
from moav_hr.core.ontology.ns import MOACV
from moav_hr.core.ontology.shapes_llc import validar_llc
from moav_hr.instances.hr import entorno
from moav_hr.instances.hr.equipo_llc import NOMBRE_ROL, ROLES, EquipoLLC

TITULO_ROL = {"parser": "Parser", "matcher": "Semantic Matcher",
              "bias_auditor": "Bias Auditor (Ω en la cadena)", "explainer": "Explainer"}
NOMBRE_REGISTRO = {"igual": "igual (P + 1, K + 1)", "similar": "similar (P = 1, K = K + 1)",
                   "nueva": "nueva (P = 1, K = 1)"}


# ------------------------------ formato ------------------------------
def _v(x) -> str:
    if isinstance(x, bool):
        return "sí" if x else "no"
    if isinstance(x, float):
        return num(x, 3)
    if isinstance(x, dict):
        return ", ".join(f"{k} = {_v(v)}" for k, v in x.items())
    if isinstance(x, (list, tuple)):
        return ", ".join(_v(v) for v in x)
    return str(x)


def _clave(c: str) -> str:
    """Clave [Q(Si), A, Q(Sf)] de la teoría en forma legible: Si → A → Sf."""
    si, a, sf = json.loads(c)
    return f"{_v(json.loads(si))} → {a} → {_v(json.loads(sf))}"


def _candidatas(reg: dict) -> list[str]:
    if not reg["candidatas"]:
        return ["ninguna teoría en la celda"]
    return [f"{c['puesto']}. T{c['id']} · {c['a']} · Sf {_v(c['sf'])} · U {num(c['u_tarea'], 3)} · "
            f"P {c['p']} · K {c['k']}" for c in reg["candidatas"]]


def _motivo(reg: dict) -> str:
    m = reg["motivo"]
    if m == "celda":
        return f"plan: T{reg['teoria_plan']}, primera del orden de la Fig. 4.21 (U ≥ 0,5)"
    if m == "similitud":
        return f"plan por similitud (respaldo, DE-2): T{reg['teoria_plan']}"
    if m == "azar_no_probada":
        return "«azar» (DE-3): primera acción todavía no probada en la celda"
    if m == "azar_bio":
        return "«azar» (DE-3): sin plan válido, operador BIO"
    if m == "regla_certificada":
        return "regla certificada (DE-6): la teoría no decide"
    return m


def _r7(reg: dict) -> str:
    ev = reg.get("evolucion")
    if ev is None:
        if reg.get("sin_r7"):
            return f"no se evalúa: {reg['sin_r7']}"
        return "no se evalúa en este ciclo (se evalúa al cierre de cada intervalo de 20)"
    pct_tn = "no aplica" if ev["pct_tn"] is None else num(ev["pct_tn"], 1)
    lcb = (ev.get("evidencia_sesgo") or {}).get("lcb")
    return (f"evaluada (ciclo {ev['ciclo_capa']} de la capa {ev['capa']}): CE_a {ev['ce_a']}, "
            f"CE_0 {ev['ce_0']}, %CEA {num(ev['pct_cea'], 1)} frente a %RCE {ev['rce']}; %TN "
            f"{pct_tn}; Ω: LCB {num(lcb, 3) if lcb is not None else '—'} frente a τ_b → "
            f"{'aprueba' if ev['gate_omega'] else 'niega'}; "
            f"{ev['estado_antes']} → {ev['estado_despues']}")


def _tabla_rol(rol: str, reg: dict, agente: str) -> dict:
    est = reg["estadisticas"]
    filas = [
        ("R1 · situación inicial", "Si (percepción)", _v(reg["si"])),
        ("R2 · acción", "candidatas en la celda (orden de la Fig. 4.21)", _candidatas(reg)),
        ("R2 · acción", "acción tomada", f"{reg['accion']} — {_motivo(reg)}"),
        ("R2 · acción", "operador BIO (lo que haría el SAR neutro)", reg["accion_bio"]),
        ("R3 · situación final", "Sf", _v(reg["sf"])),
        ("R3 · situación final", "quién la da", reg["fuente_sf"]),
        ("R4 · utilidad", "u del ciclo", num(reg["u_tarea"], 2)),
        ("R5 · aprendizaje", "registro de la Fig. 4.13",
         f"T{reg['teoria_registrada']}: {NOMBRE_REGISTRO[reg['registro']]}"),
        ("R5 · aprendizaje", "P, K y U de la teoría después del ciclo",
         f"P {reg['p']} · K {reg['k']} · U {num(reg['u'], 3)}"),
        ("R6 · estadísticas", "ciclo exitoso · acumulados del rol",
         f"{_v(bool(reg['exitoso']))} · ciclos {est['ciclos']}, exitosos "
         f"{est['ciclos_exitosos']}, teorías {est['teorias_acumuladas']}, azares {est['azares']}"),
        ("R7 · evolución", "regla de la Fig. 4.28 ∧ gate de Ω", _r7(reg)),
    ]
    return {"rol": rol, "titulo": TITULO_ROL[rol],
            "subtitulo": f"agente {agente} · estado {reg['estado']} · capa {reg['capa']} · "
                         f"ciclo {reg['ciclo']} del rol", "filas": filas}


def traza_caso(eq: EquipoLLC, ce, g) -> dict:
    v = next(x for x in eq.ventanas if x.id == ce.ventana)
    secciones = []
    for rol in ("parser", "matcher"):
        secciones.append(_tabla_rol(rol, ce.ciclos[rol], eq.agentes[rol].name))
    secciones[0]["extra"] = [
        ("plantilla del documento", f"{ce.plantilla + 1} ({_v(entorno.CELDAS_PARSER[ce.plantilla])})"
         + (" · con defecto (falta la educación)" if ce.defecto else "")),
        ("perfil extraído", _v({k: v for k, v in ce.perfil.items()})),
        ("validación del shape del perfil", f"completitud {ce.validacion_perfil['completitud']}, "
         f"fuga {_v(ce.validacion_perfil['fuga'])}, faltan "
         f"{_v(ce.validacion_perfil['faltan']) or 'nada'}")]
    secciones[1]["extra"] = [("decisión del Matcher", ce.decision_matcher)]
    aud = _tabla_rol("bias_auditor", v.ciclo_auditor, eq.agentes["bias_auditor"].name)
    aud["subtitulo"] += f" · un ciclo por ventana ({v.id}, {len(v.casos)} casos)"
    aud["extra"] = [("medida de la ventana (decisiones del Matcher)",
                     f"brecha de paridad {num(v.medida['brecha_dp'], 3)}, LCB "
                     f"{num(v.medida['lcb'], 3)}, n mínimo por grupo "
                     f"{v.medida['n_min_por_grupo']}, τ_b {num(eq.cfg['omega']['tau_b'], 3)}")]
    secciones.append(aud)
    secciones.append({"rol": "orchestrator", "titulo": "Orchestrator",
                      "subtitulo": "sin base de teorías (DE-7): infraestructura de la capa BIO",
                      "filas": [("decisión final", "registrada en la región 7 del trail",
                                 ce.decision_final),
                                ("escalamiento", "ventana derivada por el Bias Auditor",
                                 _v(ce.decision_final == "ESCALATE_HUMAN"))]})
    exp = _tabla_rol("explainer", ce.ciclos["explainer"], eq.agentes["explainer"].name)
    exp["extra"] = [(f"elemento «{k}»", t) for k, t in ce.explicacion.items()] + [
        ("verificación contra el grafo del caso",
         f"requisitos: {_v(sorted(entorno.requisitos_explicacion(ce.si_explainer)))}; faltan: "
         f"{_v(ce.verificacion_explicacion['faltan']) or 'nada'}; inconsistentes: "
         f"{_v(ce.verificacion_explicacion['inconsistentes']) or 'nada'}")]
    secciones.append(exp)
    intervinieron = Q.teorias_de_decision(g, ce.trace_id)
    return {"caso": f"{ce.escenario}-{ce.numero:03d}", "nombre": ce.caso.candidato.name,
            "escenario": ce.escenario, "ventana": ce.ventana, "trace_id": ce.trace_id,
            "documento": ce.documento, "estados": {r: ce.ciclos[r]["estado"] for r in ROLES},
            "secciones": secciones, "intervinieron": intervinieron}


# ------------------------------ Markdown y HTML ------------------------------
def _md_celda(x) -> str:
    if isinstance(x, list):
        x = "<br>".join(x)
    return str(x).replace("|", "\\|").replace("\n", "<br>")


COL_TEORIA = "Teoría usada como plan: Si → A → Sf (P, K y U al final de la corrida)"


def _md_intervinieron(filas: list[dict]) -> list[str]:
    L = [f"| Rol | Ciclo | Capa | Estado | Acción | Motivo | {COL_TEORIA} |",
         "|---|---|---|---|---|---|---|"]
    for f in filas:
        teoria = ("—" if f.get("clave") is None else _md_celda(
            f"{_clave(f['clave'])} (P {f['p']}, K {f['k']}, U {num(f['u'], 3)})"))
        L.append(f"| {f['rol']} | {f['n']} | {f['capa']} | {f['estado']} | {f['accion']} | "
                 f"{f['motivo']} | {teoria} |")
    return L


def escribir_md(t: dict, mermaid: str) -> str:
    L = encabezado_md(f"P4 · Traza del caso {t['caso']}")
    L += [f"Escenario **{t['escenario']}** · ventana **{t['ventana']}** · traza `{t['trace_id']}`.",
          "", "Estados de los roles al procesar el caso (ganados en su propio ciclo de vida): "
          + "; ".join(f"{NOMBRE_ROL[r]} **{e}**" for r, e in t["estados"].items())
          + ". El Orchestrator no tiene teorías (DE-7).", "",
          "## El DAG de la ventana (LangGraph)", "", "```mermaid", mermaid.strip(), "```", "",
          "## Documento recibido", "",
          "El CV trae datos personales, como uno real. El perfil extraído no los retiene "
          "(fuga = no) y la Si de ningún rol los contiene (DE-4).", "", "```",
          json.dumps(t["documento"], ensure_ascii=False, indent=1)
          if isinstance(t["documento"], dict) else t["documento"], "```", ""]
    for s in t["secciones"]:
        L += [f"## {s['titulo']}", "", f"*{mayus(s['subtitulo'])}.*", "",
              "| Región | Qué | Valor |", "|---|---|---|"]
        for reg, que, val in s["filas"]:
            L.append(f"| {reg} | {que} | {_md_celda(val)} |")
        if s.get("extra"):
            L += [""] + [f"- **{mayus(k)}:** {_md_celda(v)}" for k, v in s["extra"]]
        L.append("")
    L += ["## Qué teorías intervinieron en la decisión (SPARQL sobre `p4_equipo.ttl`)", ""]
    L += _md_intervinieron(t["intervinieron"]) + [""]
    return "\n".join(L) + "\n"


_CSS = """
:root { --fondo: #ffffff; --texto: #111111; --borde: #b9b9b9; --cabeza: #1F3A5F;
        --suave: #eef2f7; --acento: #0F5C46; }
@media (prefers-color-scheme: dark) {
  :root { --fondo: #15181c; --texto: #ececec; --borde: #4a4f57; --cabeza: #9cc2ff;
          --suave: #20252c; --acento: #7fd8b4; } }
body { background: var(--fondo); color: var(--texto); margin: 0;
       font: 16px/1.5 -apple-system, "Segoe UI", Roboto, sans-serif; }
main { max-width: 1100px; margin: 0 auto; padding: 24px 16px 48px; }
h1 { font-size: 26px; margin: 0 0 8px; } h2 { font-size: 20px; color: var(--cabeza);
     margin: 32px 0 4px; }
.rotulos { border-left: 4px solid var(--acento); padding: 6px 12px; background: var(--suave);
           font-style: italic; }
.sub { margin: 0 0 8px; font-style: italic; }
.tabla { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 15px; }
th, td { border: 1px solid var(--borde); padding: 6px 8px; vertical-align: top; text-align: left; }
th { background: var(--suave); }
td:first-child { white-space: nowrap; font-weight: 600; }
pre { background: var(--suave); padding: 10px; overflow-x: auto; font-size: 14px; }
ul.extra { margin: 8px 0 0; }
"""


def _h(x) -> str:
    if isinstance(x, list):
        return "<br>".join(html.escape(str(v)) for v in x)
    return html.escape(str(x))


def escribir_html(t: dict) -> str:
    p = ["<!doctype html>", "<html lang=\"es\"><head><meta charset=\"utf-8\">",
         "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
         f"<title>Traza {html.escape(t['caso'])}</title><style>{_CSS}</style></head><body><main>",
         f"<h1>P4 · Traza del caso {html.escape(t['caso'])}</h1>",
         "<p class=\"rotulos\">" + " · ".join(html.escape(mayus(r)) + "." for r in ROTULOS)
         + " Generado por código: ningún número está escrito a mano.</p>",
         f"<p>Escenario <b>{t['escenario']}</b> · ventana <b>{t['ventana']}</b> · traza "
         f"<code>{html.escape(t['trace_id'])}</code>.</p>",
         "<p>Estados de los roles al procesar el caso (ganados en su propio ciclo de vida): "
         + "; ".join(f"{NOMBRE_ROL[r]} <b>{e}</b>" for r, e in t["estados"].items())
         + ". El Orchestrator no tiene teorías (DE-7). DAG de la ventana (LangGraph): Parser → "
         "Semantic Matcher → Bias Auditor → Orchestrator → Explainer.</p>",
         "<h2>Documento recibido</h2><p>El CV trae datos personales, como uno real. El perfil "
         "extraído no los retiene y la Si de ningún rol los contiene (DE-4).</p>",
         "<pre>" + html.escape(json.dumps(t["documento"], ensure_ascii=False, indent=1)
                               if isinstance(t["documento"], dict) else t["documento"])
         + "</pre>"]
    for s in t["secciones"]:
        p += [f"<h2>{html.escape(s['titulo'])}</h2>",
              f"<p class=\"sub\">{html.escape(mayus(s['subtitulo']))}.</p>",
              "<div class=\"tabla\"><table><tr><th>Región</th><th>Qué</th><th>Valor</th></tr>"]
        for reg, que, val in s["filas"]:
            p.append(f"<tr><td>{_h(reg)}</td><td>{_h(que)}</td><td>{_h(val)}</td></tr>")
        p.append("</table></div>")
        if s.get("extra"):
            p.append("<ul class=\"extra\">" + "".join(
                f"<li><b>{_h(mayus(k))}:</b> {_h(v)}</li>" for k, v in s["extra"]) + "</ul>")
    p += ["<h2>Qué teorías intervinieron en la decisión (SPARQL sobre p4_equipo.ttl)</h2>",
          "<div class=\"tabla\"><table><tr><th>Rol</th><th>Ciclo</th><th>Capa</th><th>Estado</th>"
          f"<th>Acción</th><th>Motivo</th><th>{COL_TEORIA}</th></tr>"]
    for f in t["intervinieron"]:
        teoria = ("—" if f.get("clave") is None else
                  f"{_clave(f['clave'])} (P {f['p']}, K {f['k']}, U {num(f['u'], 3)})")
        p.append(f"<tr><td>{_h(f['rol'])}</td><td>{f['n']}</td><td>{_h(f['capa'])}</td>"
                 f"<td>{_h(f['estado'])}</td><td>{_h(f['accion'])}</td><td>{_h(f['motivo'])}</td>"
                 f"<td>{_h(teoria)}</td></tr>")
    p += ["</table></div>", "</main></body></html>"]
    return "\n".join(p) + "\n"


# ------------------------------ SHACL y SPARQL ------------------------------
def _clases(g) -> dict:
    return {c: len(set(g.subjects(RDF.type, MOACV[c])))
            for c in ("Teoria", "CicloLLC", "RegionLLC", "Decision", "LecturaEquidad")}


def escribir_shacl(g, destino) -> dict:
    conforma, texto, _ = validar_llc(g)
    t = next(iter(sorted(g.subjects(predicate=MOACV.celda))))
    g1 = copy.deepcopy(g)
    g1.set((t, MOACV.P, Literal(int(g1.value(t, MOACV.P)) + 1, datatype=XSD.integer)))
    c1, txt1, _ = validar_llc(g1)
    r1 = next(iter(sorted(g.subjects(RDF.type, MOACV.SituacionInicialLLC))))
    g2 = copy.deepcopy(g)
    g2.set((r1, MOACV.valor, Literal(json.dumps({"si": {"origen": "SY"}}))))
    c2, txt2, _ = validar_llc(g2)
    L = ["P4 · Validación SHACL de p4_equipo.ttl", ""] + [mayus(r) + "." for r in ROTULOS] + [
        "Generado por código.", "",
        "Shapes: shapes.py (TeoriaShape: P ≤ K y U en [0, 1]; AgenteShape) + shapes_llc.py",
        "(TeoriaLLCShape con ΣP = K por celda (Si, A) como restricción SPARQL, Fig. 4.13 y",
        "p. 113; CicloLLCShape con siete regiones; RegionLLCShape; SituacionInicialSinAtributo-",
        "Shape, DE-4; DecisionLLCShape; LecturaEquidadShape).", "",
        f"Tripletas: {len(g)}. Nodos por clase: " + ", ".join(f"{k} {v}" for k, v in
                                                            _clases(g).items()) + ".", "",
        f"CONFORMA: {'sí' if conforma else 'no'}", "", texto.strip(), "",
        "--- Prueba negativa 1: copia del grafo con P + 1 en una teoría ---",
        f"Teoría alterada: {t}", f"CONFORMA: {'sí' if c1 else 'no'}", "",
        "\n".join(x for x in txt1.splitlines() if "Message" in x or "Focus Node" in x)[:2000], "",
        "--- Prueba negativa 2: copia del grafo con un atributo protegido en una región 1 ---",
        f"Región alterada: {r1}", f"CONFORMA: {'sí' if c2 else 'no'}", "",
        "\n".join(x for x in txt2.splitlines() if "Message" in x or "Focus Node" in x)[:2000], ""]
    (destino / "p4_shacl.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    return {"conforma": conforma, "negativa_sigma_p": not c1, "negativa_de4": not c2,
            "tripletas": len(g), "clases": _clases(g)}


def _md_tabla(filas: list[dict], columnas: list[str]) -> list[str]:
    L = ["| " + " | ".join(columnas) + " |", "|" + "---|" * len(columnas)]
    for f in filas:
        L.append("| " + " | ".join(_md_celda(num(f[c], 3) if isinstance(f.get(c), float) else
                                              ("—" if f.get(c) is None else f[c]))
                                   for c in columnas) + " |")
    return L


def escribir_sparql(g, eq: EquipoLLC, trazas: list, destino) -> dict:
    ce_ult = trazas[-1][1]
    reg = ce_ult.ciclos["matcher"]
    base = eq.agentes["matcher"].theories
    t = next((x for x in base.theories if x.id == reg["teoria_plan"]), None)
    regla = "la teoría que fue plan del Matcher en el último caso trazado"
    if t is None:
        t = max(base.theories, key=lambda x: (x.p, -x.id))
        regla = "la teoría del Matcher con mayor P (el último caso trazado no tuvo plan)"
    iri = theory_iri(eq.agentes["matcher"].name, t, base.q)
    gen = Q.genealogia(g, iri)
    estados = Q.teorias_por_rol_y_estado(g)
    fav = Q.favorable_por_rol_y_grupo(g)
    brecha = Q.brecha_por_rol(fav)
    L = encabezado_md("P4 · Consultas SPARQL sobre la ABox del equipo (`p4_equipo.ttl`)")
    L += ["Consultas de `src/moav_hr/core/ontology/queries_llc.py`, corridas con rdflib sobre "
          "el grafo exportado.", "",
          "## 1. Genealogía de una teoría", "", f"Teoría elegida por regla fija: {regla} "
          f"(`{iri}`).", "", "```sparql", Q.Q_GENEALOGIA.strip(), "```", ""]
    L += _md_tabla([dict(f, clave=_clave(f["clave"])) for f in gen["filas"]],
                   ["rol", "clave", "p", "k", "u", "n", "capa", "estado", "refuerzos",
                    "donante"])
    capas = sorted({r["capa"] for r in gen["refuerzos"]})
    L += ["", f"Nació en el ciclo {gen['filas'][0]['n']} del Matcher (región 5) y se reforzó "
          f"en {len(gen['refuerzos'])} ciclos" + (f" (capas {', '.join(capas)})." if capas
                                                  else ".")
          + " Sin `prov:wasDerivedFrom`: en P4 no hubo compartición (E5).", "",
          "## 2. Qué teorías de qué roles intervinieron en la decisión X", "",
          "```sparql", Q.Q_TEORIAS_DE_DECISION.strip(), "```", ""]
    for nombre, ce in trazas:
        L += [f"**{nombre}** (`{ce.trace_id}`, decisión final {ce.decision_final}):", ""]
        L += _md_intervinieron(Q.teorias_de_decision(g, ce.trace_id)) + [""]
    L += ["## 3. Teorías por rol y estado del agente al nacer la teoría", "", "```sparql",
          Q.Q_TEORIAS_POR_ROL_Y_ESTADO.strip(), "```", ""]
    L += _md_tabla(estados, ["rol", "estado", "teorias", "sumaP", "exitosas"])
    L += ["", "## 4. Resultado favorable por rol y grupo (plano de auditoría; base de e_rol)",
          "", "Resultado favorable: decisión ADVANCE (Matcher), perfil completo (Parser), "
          "explicación completa (Explainer), ventana derivada (Bias Auditor). La brecha entre "
          "grupos se calcula en Python con las filas de la consulta.", "", "```sparql",
          Q.Q_FAVORABLE_POR_ROL_Y_GRUPO.strip(), "```", ""]
    L += _md_tabla(fav, ["rol", "grupo", "n", "favorables"])
    L += ["", "| Rol | Tasa AR | Tasa no-AR | Brecha |", "|---|---|---|---|"]
    for r, b in brecha.items():
        L.append(f"| {r} | {num(b['tasas'].get('AR', 0.0), 3)} | "
                 f"{num(b['tasas'].get('no-AR', 0.0), 3)} | "
                 f"{'—' if b['brecha'] is None else num(b['brecha'], 3)} |")
    (destino / "p4_sparql.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return {"genealogia": gen, "teorias_por_rol_y_estado": estados,
            "favorable_por_rol_y_grupo": fav, "brecha_por_rol": brecha}


# ------------------------------ análisis para el informe ------------------------------
def _tasa(xs: list[bool]):
    return round(sum(xs) / len(xs), 4) if xs else None


def analisis_cadena(eq: EquipoLLC) -> dict:
    """Por escenario y grupo: calificados (verdad), perfiles completos y ADVANCE del Matcher."""
    out = {}
    for esc in eq.eq["flujo"]:
        cs = [ce for ce in eq.casos if ce.escenario == esc]
        fila = {}
        for gr in ("AR", "no-AR"):
            x = [ce for ce in cs if ce.grupo == gr]
            fila[gr] = {
                "casos": len(x),
                "calificados": _tasa([ce.caso.calificado for ce in x]),
                "perfil_completo": _tasa([ce.validacion_perfil["completitud"] == "completo"
                                          for ce in x]),
                "advance_matcher": _tasa([ce.decision_matcher == "ADVANCE" for ce in x]),
                "advance_con_perfil_completo": _tasa(
                    [ce.decision_matcher == "ADVANCE" for ce in x
                     if ce.validacion_perfil["completitud"] == "completo"]),
                "aciertos_matcher": _tasa([ce.ciclos["matcher"]["u_tarea"] == 1.0 for ce in x])}
        out[esc] = fila
    return out


def celdas_sin_exito(motor, capa: str = "WIO") -> list[dict]:
    """Celdas de Si en las que el rol no tuvo ningún ciclo exitoso en la capa."""
    celdas: dict = {}
    for r in motor.ciclos:
        if r["capa"] != capa:
            continue
        x = celdas.setdefault(json.dumps(r["si"], sort_keys=True, ensure_ascii=False),
                              {"si": r["si"], "ciclos": 0, "exitosos": 0, "motivos": {}})
        x["ciclos"] += 1
        x["exitosos"] += int(r["exitoso"])
        x["motivos"][r["motivo"]] = x["motivos"].get(r["motivo"], 0) + 1
    return sorted((x for x in celdas.values() if x["exitosos"] == 0),
                  key=lambda x: -x["ciclos"])


def _evaluaciones(motor) -> list[dict]:
    return [{k: e[k] for k in ("ciclo", "capa", "ciclo_capa", "ce_a", "ce_0", "pct_cea",
                                "teorias_nuevas", "pct_tn", "gate_omega", "estado_antes",
                                "estado_despues")}
            | {"lcb": (e.get("evidencia_sesgo") or {}).get("lcb"),
               "brecha": (e.get("evidencia_sesgo") or {}).get("brecha")}
            for e in motor.evaluaciones]


def _motivos(motor) -> dict:
    out: dict = {}
    for r in motor.ciclos:
        out.setdefault(r["capa"], {}).setdefault(r["motivo"], 0)
        out[r["capa"]][r["motivo"]] += 1
    return out


def correr(out=None) -> dict:
    cfg = cargar_config()
    destino = out_dir(out)
    eq = EquipoLLC("A", cfg)
    eq.correr()
    decisiones = [{"trace_id": ce.trace_id, "resultado": ce.decision_final,
                   "ciclos": {r: reg["ciclo"] for r, reg in ce.ciclos.items()}}
                  for ce in eq.casos]
    g = abox_equipo([(r, eq.agentes[r], eq.motores[r]) for r in ROLES], decisiones)
    (destino / "p4_equipo.ttl").write_text(g.serialize(format="turtle"), encoding="utf-8")
    shacl = escribir_shacl(g, destino)
    mermaid = eq.grafo.get_graph().draw_mermaid()
    trazas, archivos = [], []
    for esc, n in eq.eq["casos_traza"].items():
        ce = next(x for x in eq.casos if x.escenario == esc and x.numero == n)
        t = traza_caso(eq, ce, g)
        for ext, texto in (("md", escribir_md(t, mermaid)), ("html", escribir_html(t))):
            ruta = destino / f"p4_traza_{t['caso']}.{ext}"
            ruta.write_text(texto, encoding="utf-8")
            archivos.append(ruta.name)
        trazas.append((t["caso"], ce))
    sparql = escribir_sparql(g, eq, trazas, destino)
    res = {"equipo": eq.resumen(), "config_equipo": cfg["equipo_e4"],
           "estados_finales": eq.estados(),
           "evaluaciones": {r: _evaluaciones(eq.motores[r]) for r in ROLES},
           "motivos_por_capa": {r: _motivos(eq.motores[r]) for r in ROLES},
           "ventanas": [{"id": v.id, **v.medida, "accion": v.ciclo_auditor["accion"],
                         "sf": v.ciclo_auditor["sf"], "u": v.ciclo_auditor["u_tarea"]}
                        for v in eq.ventanas],
           "decisiones_finales": {d: sum(ce.decision_final == d for ce in eq.casos)
                                  for d in ("ADVANCE", "REJECT", "ESCALATE_HUMAN")},
           "tipos_explicacion": {f"{s['tipo']} · {s['destinatario']} · {s['motivos']}": n
                                 for s, n in _contar([ce.si_explainer for ce in eq.casos])},
           "analisis_cadena": analisis_cadena(eq),
           "celdas_sin_exito_en_wio": {r: celdas_sin_exito(eq.motores[r])
                                       for r in ("parser", "matcher", "explainer")},
           "shacl": shacl, "sparql": {k: v for k, v in sparql.items() if k != "genealogia"},
           "genealogia": sparql["genealogia"], "trazas": archivos,
           "dag_mermaid": mermaid}
    guardar_json(res, "p4_equipo.json", destino)
    return res


def _contar(sis: list[dict]) -> list:
    vistos: dict = {}
    for s in sis:
        clave = json.dumps(s, sort_keys=True)
        vistos[clave] = vistos.get(clave, 0) + 1
    return [(json.loads(k), n) for k, n in sorted(vistos.items())]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None)
    r = correr(ap.parse_args().out)
    print(json.dumps({"estados": r["estados_finales"], "shacl": r["shacl"],
                      "trazas": r["trazas"]}, ensure_ascii=False, indent=1))
