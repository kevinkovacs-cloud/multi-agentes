#!/usr/bin/env python
"""
Informe del punto de control de E3 (Bloque E): escribe docs/parada_tecnica/E3_PUNTO_DE_CONTROL.md
desde las salidas de P1 v2, P2b v2 y P2a. Ningún número a mano.

Uso:  python experiments/parada_tecnica/informe_e3.py [--out DIR] [--correr]
"""
from __future__ import annotations
import argparse
import json

from comun_pt import encabezado_md, num, out_dir


def escribir(out=None) -> str:
    base = out_dir(out)
    v2 = base / "v2"
    p1 = json.loads((v2 / "p1.json").read_text(encoding="utf-8"))
    p2a = json.loads((v2 / "p2a.json").read_text(encoding="utf-8"))
    L = encabezado_md("E3 · Punto de control del Bloque E (punto 2a del pedido)")
    L += ["Rama `eje1/bloque-e`, sin push. Reglas del pre-registro v2 (`E2_PREREGISTRO_v2.md`), "
          "commiteado antes de correr.", "",
          "## E2 v2 (P1 y P2b), con la v1 al lado", "",
          f"- **P1 v2:** estado final **{p1['resultado']['estado_final']}** en "
          f"{p1['resultado']['ciclos']} ciclos; promociones: "
          + ("; ".join(f"ciclo {e['ciclo']}: {e['estado_antes']} → {e['estado_despues']}"
                       for e in p1["evaluaciones"] if e["promueve"]) or "ninguna") + ".",
          "- **Comparación lado a lado:** `docs/parada_tecnica/E2_v1_vs_v2.md`. Informes completos "
          "(traza, evaluaciones de R7, regla de validez, desacuerdos Fig. 4.21 / Alg. 4.7, "
          "resultados no esperados): `docs/parada_tecnica/v1/E2_PUNTO_DE_CONTROL.md` y "
          "`docs/parada_tecnica/v2/E2_PUNTO_DE_CONTROL.md`.",
          "- **Característica del gate v2:** `docs/parada_tecnica/p1_gate_caracteristica.png`.", "",
          "## E3 · Compartición (P2a)", "",
          "Detalle: `docs/parada_tecnica/v2/p2a_compartir.md`; procedencia: "
          "`docs/parada_tecnica/v2/p2a_procedencia.ttl`.", "",
          "| Equipo | Estado ganado | Ciclos | Ventanas de historia |", "|---|---|---|---|"]
    for k, h in p2a["agentes"].items():
        L.append(f"| {k} | {h['estado']} | {h['ciclos']} | {h['ventanas']} |")
    L.append("")
    R = []
    if p2a.get("detenido"):
        L += [f"**Detenido:** {p2a['motivo']}.", ""]
        R.append(f"E3 se detuvo: {p2a['motivo']}.")
    else:
        nombres = {"colaboracion_A_B": "Colaboración A → B", "cooperacion_B_C": "Cooperación B ↔ C",
                   "contraejemplo_cooperacion_A_B": "Contraejemplo: cooperación A ↔ B",
                   "contraejemplo_colaboracion_B_A": "Contraejemplo: colaboración B → A"}
        L += ["| Operación | Resultado | Motivo | Igual · similar · nueva | ΣP = K |",
              "|---|---|---|---|---|"]
        for k, r in p2a["operaciones"].items():
            cnt = (f"{r['conteo']['igual']} · {r['conteo']['similar']} · {r['conteo']['nueva']}"
                   if r["aceptada"] else "—")
            inv = ("se cumple" if r.get("invariante_receptor") else "NO") if r["aceptada"] else "—"
            L.append(f"| {nombres[k]} | {'aceptada' if r['aceptada'] else 'rechazada'} | "
                     f"{r['motivo'].replace('|', '/')} | {cnt} | {inv} |")
        L.append("")
        for nombre, seg in p2a["seguimiento"].items():
            p = seg["planificador_del_receptor"]
            L.append(f"- **{nombre.replace('*', chr(92) + '*')}** ({seg['clave'][1]}, Sf {seg['clave'][2]}): en A (P, K, U) = "
                     f"({seg['en_donante']['p']}, {seg['en_donante']['k']}, "
                     f"{num(seg['en_donante']['u'], 3)}); en B = "
                     + ("—" if seg["en_receptor"] is None else
                        f"({seg['en_receptor']['p']}, {seg['en_receptor']['k']}, "
                        f"{num(seg['en_receptor']['u'], 3)})")
                     + f"; prov:wasDerivedFrom: {len(seg['prov_wasDerivedFrom'])}; el planificador "
                     f"de B la elige: {'sí' if p['elige_esta_teoria'] else 'no'} "
                     f"({p['accion']}, {p['motivo']}).")
        L.append("")
        op = p2a["operaciones"]
        co = op["cooperacion_B_C"]
        if not co["aceptada"]:
            vent = {o_ag: o["ventanas"] for o_ag, o in co["omega"].items()}
            R.append("**La cooperación B ↔ C se rechazó por historia mínima (A9):** "
                     + ", ".join(f"{a} tiene {v} ventana{'s' if v != 1 else ''}" for a, v in vent.items())
                     + f" y `can_donate` exige {p2a_m0(op)}. B y C ganan Novice al cierre de "
                     "un intervalo temprano de BIO, así que llegan a la cooperación con menos "
                     "ventanas que las que pide A9: con estas reglas, dos Novice recién promovidos "
                     "no pueden cooperar. La mecánica de la cooperación (base común, ΣP = K) está "
                     "verificada en `tests/test_bloquee_compartir.py`.")
        ca = op["colaboracion_A_B"]
        if ca["aceptada"] and ca["conteo"]["similar"] == 0:
            R.append("En la colaboración A → B no aparecieron teorías similares.")
        omegas = [o for r in op.values() for o in r["omega"].values()]
        if omegas and all(o["evidencia_sesgo"]["aprueba"] for o in omegas):
            R.append("**Ω no encontró evidencia de sesgo en ningún donante** (LCB = "
                     + ", ".join(sorted({num(o["evidencia_sesgo"]["lcb"], 3) for o in omegas
                                         if o["evidencia_sesgo"]["lcb"] is not None}))
                     + "): misma contracara que en la evolución; con estas historias solo frenaría "
                     "ante brechas grandes.")
        for nombre, seg in p2a["seguimiento"].items():
            if not seg["planificador_del_receptor"]["elige_esta_teoria"]:
                esc = nombre.replace("*", chr(92) + "*")
                R.append(f"**El planificador de B no elige {esc}** ante un caso con su Si: elige "
                         f"{seg['planificador_del_receptor']['accion']} "
                         f"({seg['planificador_del_receptor']['motivo']}). {esc} llegó a B "
                         "con su procedencia, pero en esa celda hay otra teoría con mayor U.")
    L += ["## Resultados que no fueron los esperados (se reportan tal cual)", ""]
    L += [f"{i + 1}. {r}" for i, r in enumerate(R)] or ["Ninguno."]
    L += ["", "## Para la dirección / para decidir (no se cambió nada)", "",
          "- **Cooperación y A9.** ¿La historia mínima del donante se mide en ventanas (hoy 3 × "
          "20 ciclos) aunque un agente pueda promover en la primera? Opciones: mantenerlo; que "
          "los pares Novice operen en TBO hasta juntar la historia antes de cooperar (requiere "
          "pre-registro); o medir A9 en decisiones.",
          "- **Pregunta vinculada a la decisión 1 de la hoja:** ¿la evolución y la compartición se "
          "condicionan a la ausencia de evidencia de sesgo (implementable a esta escala) o a la "
          "evidencia de equidad (reputación certificada, que requiere historias largas)?", ""]
    texto = "\n".join(L)
    (base / "E3_PUNTO_DE_CONTROL.md").write_text(texto, encoding="utf-8")
    return texto


def p2a_m0(op) -> str:
    import re
    for r in op.values():
        m = re.search(r"requiere ≥(\d+) ventanas", r.get("motivo", ""))
        if m:
            return f"al menos {m.group(1)}"
    return "más"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Informe del punto de control de E3")
    ap.add_argument("--out", default=None)
    ap.add_argument("--correr", action="store_true")
    a = ap.parse_args()
    if a.correr:
        import p2a_compartir
        p2a_compartir.correr(a.out)
    escribir(a.out)
    print("E3_PUNTO_DE_CONTROL.md escrito")
