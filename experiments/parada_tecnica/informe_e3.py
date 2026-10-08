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


def b_antes_de_colaborar(v2, p2a: dict) -> dict:
    """Qué decidía B en las celdas de T* y T*✓ ANTES de la colaboración A → B (reconstruye B
    con su semilla pre-registrada; no corre ninguna compartición)."""
    from comun_pt import cargar_config, guardar_json
    from p2a_compartir import _equipo_bio
    from moav_hr.core.ciclo_llc import MotorLLC
    from moav_hr.core.planificador import PlanificadorLLC
    from moav_hr.instances.hr import entorno
    cfg = cargar_config(version="v2")
    b, mb, _ = _equipo_bio(cfg, "SemanticMatcher_B", cfg["compartir"]["equipos"]["B"])
    pl = PlanificadorLLC(b.theories, mb.cfg.acciones_orden,
                         **MotorLLC.parametros_validez(mb.cfg))
    out = {}
    for nombre, seg in p2a.get("seguimiento", {}).items():
        d = pl.planificar(seg["si"], b.layer.value, entorno.operador_bio_matcher(seg["si"]))
        out[nombre] = {"capa": b.layer.value, "accion": d.accion, "motivo": d.motivo,
                       "candidatas": d.candidatas}
    guardar_json({"demo": "E3 — decisión de B antes de la colaboración A → B", "decisiones": out},
                 "p2a_b_antes_de_colaborar.json", v2)
    return out


def escribir(out=None) -> str:
    base = out_dir(out)
    v2 = base / "v2"
    p1 = json.loads((v2 / "p1.json").read_text(encoding="utf-8"))
    p2a = json.loads((v2 / "p2a.json").read_text(encoding="utf-8"))
    coop_a9 = (json.loads((v2 / "p2a_cooperacion_a9.json").read_text(encoding="utf-8"))["resultado"]
               if (v2 / "p2a_cooperacion_a9.json").exists() else None)
    antes = b_antes_de_colaborar(v2, p2a) if not p2a.get("detenido") else {}
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
        if coop_a9 is not None:
            r = coop_a9
            L += ["### Cooperación B ↔ C con A9 en decisiones (pre-registro corto, "
                  "`E3_PREREGISTRO_A9.md`)", "",
                  f"- **Resultado:** {'aceptada' if r['aceptada'] else 'rechazada'} — {r['motivo']}."]
            if r["aceptada"]:
                def cuenta(c):
                    nom = {"igual": ("igual", "iguales"), "similar": ("similar", "similares"),
                           "nueva": ("nueva", "nuevas")}
                    return " · ".join(f"{c[k]} {nom[k][0] if c[k] == 1 else nom[k][1]}"
                                      for k in ("igual", "similar", "nueva"))
                L += [f"- **B en C:** {cuenta(r['conteo'])}; **C en B:** "
                      f"{cuenta(r['conteo_sentido_C_en_B'])}.",
                      f"- **Base resultante común a los dos (Alg. 4.9):** "
                      f"{'sí' if r['base_comun_a_los_dos'] else 'no'}; ΣP = K: "
                      f"{'se cumple' if r['invariante_receptor'] and r['invariante_donante'] else 'NO'}.",
                      "- **Ω en cada sentido:** " + "; ".join(
                          f"{ag}: {o['a9_decisiones']['decisiones']} decisiones, LCB "
                          f"{num(o['evidencia_sesgo']['lcb'], 3)} → {o['evidencia_sesgo']['motivo']}"
                          for ag, o in r["omega"].items()) + ".",
                      "- Lado a lado con la corrida original: "
                      "`docs/parada_tecnica/E3_cooperacion_A9_lado_a_lado.md`."]
            L.append("")
        if "T*" in antes:
            ant, seg = antes["T*"], p2a["seguimiento"]["T*"]
            des = seg["planificador_del_receptor"]
            u_ant = {c["a"]: c["u_tarea"] for c in ant["candidatas"]}
            u_des = {c["a"]: c["u_tarea"] for c in des["candidatas"]}
            L += ["### Qué cambia en la celda de T\\* al recibir la experiencia de A", "",
                  f"- **Antes de la colaboración:** B elegía {ant['accion']} ({ant['motivo']}); "
                  "U por acción: " + ", ".join(f"{a_} {num(u, 3)}" for a_, u in sorted(u_ant.items()))
                  + ".",
                  f"- **Después:** B elige {des['accion']} ({des['motivo']}); U por acción: "
                  + ", ".join(f"{a_} {num(u, 3)}" for a_, u in sorted(u_des.items())) + ".",
                  "- **Lectura:** la experiencia que transfiere A, incluida la teoría fallida T\\*, "
                  "baja la utilidad de la acción que fracasó"
                  + (f" (ADVANCE: {num(u_ant.get('ADVANCE', 0), 3)} → {num(u_des.get('ADVANCE', 0), 3)})"
                     if "ADVANCE" in u_ant and "ADVANCE" in u_des else "")
                  + (" y le da al novato un plan válido donde antes decidía por azar"
                     if ant["motivo"].startswith("azar") and des["motivo"] == "celda" else "")
                  + "." + (f" En esta corrida B no habría repetido el error de todos modos: su "
                           f"«azar» con el operador BIO ya elegía {ant['accion']}."
                           if ant["accion"] == des["accion"] else ""), ""]
        op = p2a["operaciones"]
        co = op["cooperacion_B_C"]
        if not co["aceptada"]:
            vent = {o_ag: o["ventanas"] for o_ag, o in co["omega"].items()}
            R.append("**La cooperación B ↔ C se rechazó por historia mínima (A9):** "
                     + ", ".join(f"{a} tiene {v} ventana{'s' if v != 1 else ''}" for a, v in vent.items())
                     + f" y `can_donate` exige {p2a_m0(op)}. B y C ganan Novice al cierre de "
                     "un intervalo temprano de BIO, así que llegan a la cooperación con menos "
                     "ventanas que las que pide A9."
                     + (" Con A9 en decisiones (pre-registro corto) la cooperación se "
                        + ("acepta." if coop_a9 and coop_a9["aceptada"] else "tampoco procede.")
                        if coop_a9 is not None else ""))
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
                R.append(f"**El planificador de B no elige {esc}** (una teoría fallida) ante un caso "
                         f"con su Si: elige {seg['planificador_del_receptor']['accion']} "
                         f"({seg['planificador_del_receptor']['motivo']}). Es el uso esperado de una "
                         "teoría de fracaso: resta utilidad a la acción que fracasó (ver «Qué cambia "
                         "en la celda de T\\*»).")
    L += ["## Resultados que no fueron los esperados (se reportan tal cual)", ""]
    L += [f"{i + 1}. {r}" for i, r in enumerate(R)] or ["Ninguno."]
    L += ["", "## Para la dirección / para decidir (no se cambió nada)", "",
          "- **A9 (extensión del modelo, no del LLC):** ¿la historia mínima para donar se mide "
          "en decisiones (pre-registro corto de E3) o en ventanas?",
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
        import p2a_cooperacion_a9
        p2a_compartir.correr(a.out)
        p2a_cooperacion_a9.correr(a.out)
    escribir(a.out)
    print("E3_PUNTO_DE_CONTROL.md escrito")
