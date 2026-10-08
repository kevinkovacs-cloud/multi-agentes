#!/usr/bin/env python
"""
E3 · Corrida de la cooperación B ↔ C con A9 en decisiones (pre-registro corto,
E3_PREREGISTRO_A9.md). Solo la cooperación; la colaboración A → B y los contraejemplos no
cambian. Escribe docs/parada_tecnica/v2/p2a_cooperacion_a9.json y E3_cooperacion_A9_lado_a_lado.md
(original: A9 en ventanas, tomado de p2a.json; nueva: A9 en decisiones).
"""
from __future__ import annotations
import argparse
import json

from comun_pt import cargar_config, encabezado_md, guardar_json, num, out_version
from p2a_compartir import _decisiones, _equipo_bio
from moav_hr.core.compartir_llc import clasificar, compartir
from moav_hr.core.monitor import FairnessMonitor
from moav_hr.core.theory import theory_key


def correr(out=None) -> dict:
    destino = out_version(out, "v2")
    cfg = cargar_config(version="v2")
    comp = cfg["compartir"]
    mon = FairnessMonitor(tau=cfg["omega"]["tau"], attr=cfg["omega"]["atributo"],
                          disparity_threshold=cfg["omega"]["tau_b"])
    b, mb, _ = _equipo_bio(cfg, "SemanticMatcher_B", comp["equipos"]["B"])
    c, mc, _ = _equipo_bio(cfg, "SemanticMatcher_C", comp["equipos"]["C"])
    clas_c_en_b = clasificar(c.theories, b.theories)          # el otro sentido de la cooperación
    r = compartir("cooperacion", b, c, mon, {b.name: _decisiones(mb), c.name: _decisiones(mc)},
                  comp["m0_historia_minima"], cfg["omega"]["delta"], mb.es_acierto,
                  a9=comp["a9"], a9_min=comp["a9_min_decisiones"], a9_ambos=comp["a9_ambos_grupos"])
    if r["aceptada"]:
        fb = sorted((theory_key(t, b.theories.q), t.p, t.k, round(t.u, 6)) for t in b.theories.theories)
        fc = sorted((theory_key(t, c.theories.q), t.p, t.k, round(t.u, 6)) for t in c.theories.theories)
        r["base_comun_a_los_dos"] = fb == fc
        r["conteo_sentido_C_en_B"] = {k: sum(1 for v in clas_c_en_b.values() if v == k)
                                      for k in ("igual", "similar", "nueva")}
    guardar_json({"demo": "E3 — cooperación B ↔ C con A9 en decisiones", "resultado": r},
                 "p2a_cooperacion_a9.json", destino)
    orig = json.loads((destino / "p2a.json").read_text(encoding="utf-8"))["operaciones"]["cooperacion_B_C"]
    L = encabezado_md("E3 · Cooperación B ↔ C: A9 en ventanas frente a A9 en decisiones")
    L += ["| | Original (A9 en ventanas) | Pre-registro corto (A9 en decisiones) |", "|---|---|---|"]
    for nombre, f in (
        ("Resultado", lambda x: "aceptada" if x["aceptada"] else "rechazada"),
        ("Motivo", lambda x: x["motivo"].replace("|", "/")),
        ("Ω sobre B (brecha, LCB)", lambda x: _om(x, "SemanticMatcher_B")),
        ("Ω sobre C (brecha, LCB)", lambda x: _om(x, "SemanticMatcher_C")),
        ("Historia B / C", lambda x: _hist(x)),
        ("Igual · similar · nueva (B en C)", lambda x: (f"{x['conteo']['igual']} · {x['conteo']['similar']} · "
                                                        f"{x['conteo']['nueva']}") if x["aceptada"] else "—"),
        ("Igual · similar · nueva (C en B)", lambda x: (" · ".join(str(x["conteo_sentido_C_en_B"][k])
                                                                   for k in ("igual", "similar", "nueva"))
                                                        if x.get("conteo_sentido_C_en_B") else "—")),
        ("Base resultante común (Alg. 4.9)", lambda x: ("sí" if x.get("base_comun_a_los_dos") else "no")
         if x["aceptada"] else "—"),
        ("ΣP = K en B y en C", lambda x: ("se cumple" if x["invariante_receptor"] and x["invariante_donante"]
                                          else "NO") if x["aceptada"] else "—"),
        ("Teorías de B antes → después", lambda x: f"{x['base_donante']} → {x.get('base_receptor_despues', '—')}"
         if x["aceptada"] else str(x["base_donante"]))):
        L.append(f"| {nombre} | {f(orig)} | {f(r)} |")
    if r["aceptada"]:
        L += ["", "## Teorías de B y cómo entran en C (P, K, U)", "",
              "| Si · A · Sf | Entra como | En B | En C antes | Base común después |", "|---|---|---|---|---|"]
        pk = lambda d: "—" if d is None else f"{d['p']}, {d['k']}, {num(d['u'], 3)}"  # noqa: E731
        for t in r["teorias"]:
            L.append(f"| {t['clave'][0]} · {t['clave'][1]} · {t['clave'][2]} | {t['categoria']} | "
                     f"{pk(t['en_donante'])} | {pk(t['en_receptor_antes'])} | {pk(t['en_receptor_despues'])} |")
    (destino.parent / "E3_cooperacion_A9_lado_a_lado.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return r


def _om(x, ag):
    o = x["omega"].get(ag)
    if not o:
        return "—"
    ev = o["evidencia_sesgo"]
    return f"{num(ev['brecha'], 3)}, {num(ev['lcb'], 3)} → {ev['motivo']}" if ev["lcb"] is not None else ev["motivo"]


def _hist(x):
    return " / ".join(f"{o['ventanas']} ventanas, " + (f"{o['a9_decisiones']['decisiones']} decisiones"
                                                       if "a9_decisiones" in o else "decisiones no evaluadas")
                      for o in x["omega"].values())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    r = correr(ap.parse_args().out)
    print("cooperación B ↔ C (A9 en decisiones):", "aceptada" if r["aceptada"] else "rechazada", "—", r["motivo"])
