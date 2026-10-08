#!/usr/bin/env python
"""
Pre-registro de E4 (todos los roles con su ciclo de vida y la traza completa, punto 4):
escribe docs/parada_tecnica/E4_PREREGISTRO.md a partir de las reglas 7 a 10 de
`instances/hr/entorno.py` y de la sección `equipo_e4` de `configs/parada_tecnica.yaml`.
No corre ningún agente: las tasas son valores esperados de las reglas.

Uso:  python experiments/parada_tecnica/preregistro_e4.py [--out DIR]
"""
from __future__ import annotations
import argparse

from comun_pt import cargar_config, encabezado_md, num, out_dir
from moav_hr.instances.hr import entorno

_NOMBRE = {"reglas_estrictas": "reglas estrictas", "diccionario_sinonimos": "diccionario de "
           "sinónimos", "por_factores": "por factores", "contrafactica": "contrafáctica",
           "regulatoria": "regulatoria"}


def _celda(c: dict) -> str:
    return " · ".join(c.values())


def escribir(out=None) -> str:
    cfg = cargar_config()
    eq, om, cv = cfg["equipo_e4"], cfg["omega"], cfg["ciclo_de_vida"]
    d = entorno.describir_entorno_e4(om["tau_b"], om["delta"], eq["ventana"])
    pa, ex, au = d["parser"], d["explainer"], d["auditor"]
    n_casos = sum(cv["ciclos_por_capa"][c] for c in eq["flujo"])
    n_ventanas = n_casos // eq["ventana"]
    L = encabezado_md("E4 · Pre-registro: todos los roles con su ciclo de vida (antes de correr P4)")
    L += ["Reglas fijadas **antes** de correr P4. Fuente: `src/moav_hr/instances/hr/entorno.py` "
          "(reglas 7 a 10) y `src/moav_hr/instances/hr/estrategias_llc.py`; parámetros: "
          "`configs/parada_tecnica.yaml`, sección `equipo_e4`. Los parámetros del ciclo de vida "
          "son los de la v2, iguales para todos los roles. Un test "
          "(`tests/test_bloquee_entorno_e4.py`) verifica que el código de las estrategias cumple "
          "las tablas de este documento.", "",
          "## El equipo", "",
          f"- **DAG por ventana de {eq['ventana']} casos,** orquestado con LangGraph "
          "(`core/grafo.py`): Parser → Semantic Matcher → Bias Auditor → Orchestrator → "
          "Explainer. El Orchestrator no tiene teorías (DE-7): registra la decisión final y el "
          "escalamiento.",
          f"- **Flujo de casos:** los escenarios {', '.join(eq['flujo'])} de P1 v2 (semilla "
          f"{eq['semilla_casos']}), {n_casos} casos y {n_ventanas} ventanas.",
          "- **Cada rol transita su propia capa** (la de su estado ganado) con su propio ciclo de "
          "vida: contadores, intervalos y región 7. El escenario solo fija qué casos llegan. Es "
          "una adaptación declarada: en el LLC cada SAR tiene un escenario por capa; en el DAG "
          "los roles comparten el caso.",
          "- **Capa agotada sin promoción, o Mature:** el rol sigue actuando y aprendiendo "
          "(regiones 1 a 6) sin evaluar la región 7.",
          "- **Gate de Ω de cada rol** (generalización declarada del gate v2): Ω niega la "
          "promoción si LCB_δ/L(|brecha|) > τ_b, donde la brecha es la del resultado favorable "
          "del rol entre grupos: decisión ADVANCE (Matcher), perfil completo (Parser), "
          "explicación completa (Explainer), ventana derivada (Bias Auditor). El atributo "
          "protegido sigue fuera de Si, A y los prompts (DE-4).",
          f"- **α = {num(eq['alpha'], 1)}** en P4 (LLC puro); α = 0,5 se compara en E6.", "",
          "## Parser (regla 7)", "",
          f"Operador BIO: **{_NOMBRE[pa['operador_bio']]}**. Con probabilidad "
          f"{num(pa['p_defecto'], 1)} el documento omite la educación (completo pasa a parcial). "
          "u = 1 completo, 0,5 parcial, 0 fallido o con fuga.", "",
          "| Plantilla (formato · estructura · etiquetas) | Frec. AR | Frec. no-AR | Reglas "
          "estrictas | Diccionario de sinónimos | u esperada (estrictas / diccionario) |",
          "|---|---|---|---|---|---|"]
    for c in pa["celdas"]:
        e = c["estrategias"]
        L.append(f"| {_celda(c['celda'])} | {num(c['frecuencia']['AR'])} | "
                 f"{num(c['frecuencia']['no-AR'])} | {e['reglas_estrictas']['sin_defecto']} | "
                 f"{e['diccionario_sinonimos']['sin_defecto']} | "
                 f"{num(e['reglas_estrictas']['u_esperada'], 3)} / "
                 f"{num(e['diccionario_sinonimos']['u_esperada'], 3)} |")
    L += ["", "| Grupo | P(completo) con el operador BIO | P(completo) con la mejor estrategia "
          "por plantilla |", "|---|---|---|"]
    for g, v in pa["por_grupo"].items():
        L.append(f"| {g} | {num(v['p_completo_operador_bio'], 3)} | "
                 f"{num(v['p_completo_mejor_estrategia'], 3)} |")
    brecha_bio = abs(pa["por_grupo"]["AR"]["p_completo_operador_bio"]
                     - pa["por_grupo"]["no-AR"]["p_completo_operador_bio"])
    L += ["", f"- **Canal proxy declarado (B3):** la plantilla depende del grupo; d_TV entre las "
          f"dos distribuciones de plantilla = {num(pa['dtv_formato_grupo'], 3)}. La Si del Parser "
          "no contiene el atributo protegido, pero lo deja inferir en parte.",
          f"- **Brecha esperada de completitud** con el operador BIO: {num(brecha_bio, 3)}; con la "
          "mejor estrategia por plantilla: 0. Es lo que el aprendizaje del Parser puede cerrar.",
          "- **Efecto en cadena (regla 8):** el Matcher percibe el perfil extraído. Un perfil "
          "parcial o fallido produce una Si distinta de la del candidato (educación «—», banda "
          "junior, 0 skills), fuera del catálogo de P1.", "",
          "## Explainer (regla 10)", "",
          f"Operador BIO: **{_NOMBRE[ex['operador_bio']]}**. u = 1 si la explicación está completa "
          "(verificada contra el grafo RDF del caso por SPARQL), 0 si no. Determinista por celda.",
          "", "| Si (tipo · destinatario · motivos) | Requisitos | Por factores | Contrafáctica "
          "| Regulatoria |", "|---|---|---|---|---|"]
    for c in ex["celdas"]:
        s = c["completa"]
        L.append(f"| {_celda(c['si'])} | {', '.join(c['requisitos'])} | "
                 + " | ".join("completa" if s[e] else "incompleta"
                              for e in entorno.ESTRATEGIAS_EXPLAINER) + " |")
    L += ["", "- **Elementos de cada estrategia:** " + "; ".join(
          f"{_NOMBRE[e]}: {', '.join(sorted(v))}"
          for e, v in entorno.ELEMENTOS_POR_ESTRATEGIA.items()) + ".",
          "- **Motivos** no cambia la mejor estrategia en ninguna celda: está en la Si porque lo "
          "pide la sección 6 del handoff; se informa.", "",
          "## Bias Auditor (regla 9, DE-6)", "",
          f"Un ciclo por ventana de {au['ventana']} casos ({au['n_por_grupo']} por grupo). La "
          "acción la decide la regla certificada (DERIVAR si LCB_δ(|Δ_DP|) > τ_b), no la "
          "teoría. La revisión confirma sesgo con el mismo estándar sobre la brecha de tasas de "
          "error del Matcher.", "",
          f"- **LCB más alta posible** con {au['n_por_grupo']} por grupo (brecha observada 1): "
          f"{num(au['lcb_maxima'], 4)}, frente a τ_b = {num(au['tau_b'], 3)}. "
          + ("La regla **no puede derivar** y la revisión **no puede confirmar** sesgo con "
             "ventanas de este tamaño: todas las ventanas se liberan y u = 1."
             if not au["puede_derivar"] else "La regla puede derivar."), "",
          "## Consecuencias calculables antes de correr", "",
          "1. **El Bias Auditor no puede promover con la regla de P1.** Su acción es siempre la "
          "del operador BIO (la regla certificada, DE-6), así que CE_a = CE_0 y %CEA = 0 < "
          f"%RCE = {cv['rce']}. Además, con {n_ventanas} ventanas no llega a cerrar un intervalo "
          f"de {cv['n_intervalo']} ciclos. Se informa; cómo evoluciona un rol que no decide es "
          "una pregunta para la dirección.",
          "2. **El Explainer no ve decisiones derivadas** (tipo «deriva»), porque el Auditor no "
          "puede derivar (punto anterior).",
          "3. **Matcher del equipo:** sus celdas incluyen las Si de perfiles parciales o "
          "fallidos (regla 8); su precisión en el equipo no es comparable con la de P1.", "",
          "## Qué produce P4", "",
          "- `p4_traza_<caso>.md` y `.html` para los casos pre-registrados: "
          + ", ".join(f"{c}-{n:03d}" for c, n in eq["casos_traza"].items())
          + " (primer caso de la última ventana de cada escenario). Una tabla por rol: situación "
          "inicial, candidatas y acción, situación final, P, K y U, región en que se registró y "
          "estado del agente.",
          "- `p4_equipo.ttl` (ABox del equipo), `p4_shacl.txt` (conforme o no, con ΣP = K), "
          "`p4_sparql.md` (genealogía de una teoría, teorías que intervinieron en una decisión, "
          "teorías por rol y estado, resultado favorable por rol y grupo) y `p4_equipo.json`.", ""]
    destino = out_dir(out)
    ruta = destino / "E4_PREREGISTRO.md"
    ruta.write_text("\n".join(L) + "\n", encoding="utf-8")
    return str(ruta)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None)
    print(escribir(ap.parse_args().out))
