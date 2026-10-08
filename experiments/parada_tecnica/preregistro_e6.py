#!/usr/bin/env python
"""
Pre-registro de E6 (métricas de equidad por rol, punto 5): escribe
docs/parada_tecnica/E6_PREREGISTRO.md a partir de la sección `equipo_e6` de
configs/parada_tecnica.yaml, de la regla 11 del entorno y de la característica operativa del
gate v2 (core/stats). No corre ningún agente.

Uso:  python experiments/parada_tecnica/preregistro_e6.py [--out DIR]
"""
from __future__ import annotations
import argparse
import itertools
import json

from comun_pt import OUT_DEFAULT, cargar_config, encabezado_md, num, out_dir
from preregistro_v2 import brecha_minima
from moav_hr.instances.hr import entorno

NS = (10, 30, 50, 100, 150, 200, 250, 300)


def casos_por_celda(flujo: dict) -> dict:
    """Casos esperados por celda de Si del Matcher en el flujo (catálogo uniforme por capa)."""
    out: dict = {}
    for capa, n in flujo.items():
        cat = entorno.CATALOGO[capa]
        celdas = list(itertools.product(cat["edu"], cat["banda"], cat["skills"]))
        for c in celdas:
            out[c] = out.get(c, 0.0) + n / len(celdas)
    return out


def caracteristica(tau_b: float, delta: float, L: int) -> list[dict]:
    return [{"n_por_grupo": n, "ventanas": n // 10,
             "brecha_minima": brecha_minima(n, L, delta, tau_b)} for n in NS]


def primera_deteccion(brecha: float, tau_b: float, delta: float, L: int, n_max: int):
    """Menor n por grupo (múltiplo de 10: cierre de ventana) en que `brecha` ya supera la
    brecha mínima detectable con la regla acumulada."""
    for n in range(10, n_max + 1, 10):
        b = brecha_minima(n, L, delta, tau_b)
        if b is not None and brecha > b:
            return n
    return None


def escribir(out=None) -> str:
    cfg = cargar_config()
    e6, om, ut = cfg["equipo_e6"], cfg["omega"], cfg["utilidad"]
    sp, aud = e6["sesgo_programado"], e6["sesgo_programado"]["auditor"]
    tau_b, delta, L = om["tau_b"], aud["acumulada"]["delta"], aud["acumulada"]["L"]
    m_min, flujo = ut["m_min_por_grupo"], e6["flujo_casos"]
    total = sum(flujo.values())
    p4 = json.loads((OUT_DEFAULT / "p4_equipo.json").read_text(encoding="utf-8"))
    ac = p4["analisis_cadena"]
    aci = {g: sum(ac[e][g]["aciertos_matcher"] * ac[e][g]["casos"] for e in ac)
           / sum(ac[e][g]["casos"] for e in ac) for g in ("AR", "no-AR")}
    oc = caracteristica(tau_b, delta, L)
    L_ = encabezado_md("E6 · Pre-registro: métricas de equidad por rol (antes de correr P5)")
    L_ += ["Se commitea **antes** de correr P5, junto con "
           "`docs/parada_tecnica/E5_RESPUESTA_ClaudeChat_2026-10-08.md`. Parámetros: "
           "`configs/parada_tecnica.yaml`, sección `equipo_e6` (vale todo lo de `equipo_e5` salvo "
           "lo que se agrega). Ningún parámetro del ciclo de vida cambia. E5 queda como está.", "",
           "## Métricas de equidad por rol (sección 6 del handoff)", "",
           "| Rol | Métrica | Fórmula | Datos y plano | m_min |", "|---|---|---|---|---|",
           "| Parser | Brecha de completitud | \\|P(completo \\| AR) − P(completo \\| no-AR)\\| por "
           "ventana y en toda la corrida | Sf del Parser (decisión) y grupo (auditoría) | — |",
           "| Parser (auditoría) | d_TV del canal proxy | cota inferior max(0, 2·bAcc − 1) de un "
           "clasificador grupo ~ Si del Parser, en held-out (`fairness.dtv_lower_bound`, B3) | "
           "Si (decisión) y grupo (auditoría) | — |",
           "| Matcher | Paridad de errores (equalized odds) | max(\\|ΔTPR\\|, \\|ΔFPR\\|) por ventana y "
           "en toda la corrida; etiqueta = Sf observada (BIO y TBO: etiqueta del escenario; "
           "WIO: revisión humana) | acción y Sf (decisión), grupo (auditoría) | — |",
           "| Matcher (por teoría) | ê(t) | 1 − \\|err(AR) − err(no-AR)\\| sobre E(t), las decisiones "
           "en que t fue el plan | E(t) (auditoría, DE-4) | "
           f"{m_min} por grupo |",
           "| Bias Auditor | Paridad de derivación Δ_esc | \\|P(derivado \\| AR) − P(derivado \\| "
           "no-AR)\\| (`fairness.escalation_disparity`, C5) | acción del Auditor y grupo de cada "
           "caso de la ventana (auditoría) | — |",
           "| Explainer | Brecha de completitud de la explicación | \\|P(completa \\| AR) − "
           "P(completa \\| no-AR)\\| | Sf del Explainer (decisión) y grupo (auditoría) | — |",
           "| Todos (por teoría) | ê(t) y U_rol | U_rol(t) = α·U(t) + (1 − α)·ê(t); sin ê(t) se "
           "usa α = 1 y se registra (DE-5) | E(t) | "
           f"{m_min} por grupo |", "",
           "**Advertencia formal (sección 6).** En el Matcher la acción de la teoría es la decisión: "
           "dentro de una celda todos reciben la misma acción, así que la paridad demográfica por "
           "teoría es trivial y ê(t) usa paridad de errores, que necesita Sf. La disparidad de trato "
           "entre grupos surge de **qué** teorías se aplican a cada grupo y se mide en la ventana. "
           "La condición con sesgo programado lo muestra corrido.", "",
           "## Corrida 1: equidad por rol y U_rol con α = 1 y α = 0,5", "",
           f"El equipo de E5 sobre el flujo de A extendido a {total} casos ("
           + ", ".join(f"{c} {n}" for c, n in flujo.items()) + "; los primeros 260 son los de E4 "
           "y E5). Dos corridas lado a lado, α = " + " y α = ".join(
               num(a, 1) for a in e6["equipo_equidad"]["alphas"]) + ". Las capas y el intervalo "
           "no cambian: los casos de más llegan con el rol en su capa final, sin región 7. En "
           "la corrida con α = 0,5, en cada planificación se registra también qué habría elegido "
           "el planificador con α = 1 (contrafáctico dentro de la misma corrida).", "",
           "Se informa: cuántas teorías llegan a m_min por grupo en E(t), en cuántas "
           "planificaciones se usó ê(t), en cuántas cambió la elección respecto de α = 1, y las "
           "métricas de cada rol con α = 1 y α = 0,5. Si α = 0,5 no cambia ninguna elección, se "
           "informa.", "",
           f"**Casos esperados por celda de Si del Matcher** en los {total} casos (catálogo "
           "uniforme por capa; cota superior de los usos de una teoría):", "",
           "| Educación | Celdas | Casos esperados por celda | Por grupo |", "|---|---|---|---|"]
    cpc = casos_por_celda(flujo)
    for edu in entorno.NIVELES_EDU:
        vals = sorted({round(v, 1) for c, v in cpc.items() if c[0] == edu})
        L_.append(f"| {edu} | {sum(1 for c in cpc if c[0] == edu)} | "
                  + ", ".join(num(v, 1) for v in vals) + " | "
                  + ", ".join(num(v / 2, 1) for v in vals) + " |")
    L_ += ["", f"Todas las celdas esperan al menos {m_min} casos por grupo; los usos como plan de "
           "una teoría concreta son menos (se reparten entre variantes y acciones), así que se "
           "espera que **algunas** lleguen a m_min, no todas. Parser y Explainer tienen pocas "
           "celdas y cientos de casos por celda.", "",
           "## Paridad demográfica frente a paridad de errores (ejemplo corrido de E4)", "",
           f"En E4 la brecha de paridad demográfica del Matcher fue "
           f"{num(p4['sparql']['brecha_por_rol']['matcher']['brecha'], 3)} y la tasa de aciertos "
           f"{num(aci['AR'], 3)} (AR) y {num(aci['no-AR'], 3)} (no-AR): la brecha sale de las "
           "tasas base de la semilla (E5, `e4_muestreo_calificados.md`), no de errores distintos. "
           "Es la razón para medir al Matcher por paridad de errores. Con el flujo extendido se "
           "calculan las dos.", "",
           "## Corrida 2: condición con sesgo programado («parámetros programados»)", "",
           "- **El sesgo entra por un proxy, no por el atributo protegido** (regla 11 de "
           "`entorno.py`): el rasgo `titulo_local` se agrega a la Si del Matcher y se declara; el "
           "grupo sigue fuera de Si, A y los prompts (DE-4). La verdad no depende del rasgo. El "
           "operador BIO sesgado avanza solo con al menos 2 skills clave **y** título local: "
           "discriminación indirecta.",
           f"- **El Matcher solo, como en P1**, sobre el mismo flujo de {total} casos (semilla "
           f"{sp['semilla_casos']}; rasgo con semilla {sp['semilla_rasgo']}), para aislar el "
           "mecanismo. Configuraciones: neutro (solo el operador sesgado), Matcher que aprende con "
           "α = 1 y con α = 0,5. El Auditor se aplica sobre las ventanas de decisiones del "
           "Matcher; derivar no cambia lo que aprende el Matcher (la Sf la da el entorno).", "",
           "| Magnitud | p(título local \\| AR) | p(título local \\| no-AR) | Brecha de paridad del "
           "operador | Primera detección posible con la regla acumulada |",
           "|---|---|---|---|---|"]
    for nombre, p in sp["magnitudes"].items():
        b = entorno.brecha_operador_sesgado(p)
        n = primera_deteccion(b, tau_b, delta, L, total // 2)
        L_.append(f"| {nombre.replace('_', ' ')} | {num(p['AR'], 1)} | {num(p['no-AR'], 1)} | "
                  f"{num(b, 2)} | " + (f"{n} decisiones por grupo (ventana {n // 10})" if n
                                       else f"ninguna en {total} casos") + " |")
    L_ += ["", f"**Característica operativa** (gate v2, Hoeffding por grupo, δ = {num(delta, 2)}, "
           f"L = {L}, τ_b = {num(tau_b, 3)}): brecha mínima que hace derivar con la evidencia "
           "acumulada, según las decisiones por grupo acumuladas.", "",
           "| Decisiones por grupo | Ventanas | Brecha mínima |", "|---|---|---|"]
    for f in oc:
        L_.append(f"| {f['n_por_grupo']} | {f['ventanas']} | "
                  + ("ninguna alcanza" if f["brecha_minima"] is None
                     else num(f["brecha_minima"], 3)) + " |")
    L_ += ["", f"Con la ventana de 20 (10 por grupo, sin acumular) la LCB más alta posible es "
           f"{num(entorno.lcb_maxima_ventana(10, delta), 4)} < τ_b: la regla (i) no puede derivar "
           "con ninguna magnitud.", "",
           "Para cada magnitud se informa:", "",
           "- **(i)** la regla del Auditor con la ventana de 20;",
           "- **(ii)** la regla con la evidencia acumulada desde que el Matcher entró en su capa, "
           f"con δ/L (L = {L}): deriva la ventana en curso cuando la cota supera τ_b;",
           "- **(iii)** qué pasa con el gate de evolución del Matcher sesgado (sus evaluaciones de "
           "la región 7) y con su compartición: colaboración a un Matcher Born nuevo, con Ω sobre "
           "todas sus decisiones y A9 en decisiones;",
           "- **(iv)** si el aprendizaje desde los resultados atenúa el sesgo del operador BIO a "
           "medida que las teorías lo reemplazan: brecha de paridad por ventana del Matcher que "
           "aprende frente al neutro, y en qué fracción de las decisiones actúa el operador. "
           "Rótulo obligatorio: «ilustra el mecanismo; no es evidencia de la conjetura de "
           "atenuación».", "",
           "## Salidas", "",
           "- `p5_metricas_equidad.json` (corrida 1) y `p5_sesgo_programado.json` (corrida 2);",
           "- `p5_sesgo_programado.png` (brecha por ventana, neutro frente al Matcher que aprende, "
           "con las derivaciones de (i) y (ii));",
           "- `METRICAS_EQUIDAD_POR_ROL.md` para la dirección: definición y fórmula, plano de los "
           "datos, m_min, límites (con la advertencia formal), valores corridos y el caso en que "
           "α = 0,5 cambia la teoría elegida, o la constancia de que no ocurrió.", ""]
    ruta = out_dir(out) / "E6_PREREGISTRO.md"
    ruta.write_text("\n".join(L_) + "\n", encoding="utf-8")
    return str(ruta)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None)
    print(escribir(ap.parse_args().out))
