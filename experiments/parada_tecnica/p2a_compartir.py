#!/usr/bin/env python
"""
P2a — Cómo se coopera, colabora y transfiere la teoría generada a un agente novato
(punto 2a del pedido; Bloque E · E3). Reglas del pre-registro v2 (configs/parada_tecnica.yaml).

Agentes, todos con estados GANADOS (sin fijar estados a mano):
  · A: el Matcher de P1 v2 (equipo A), con su base de teorías y su historia;
  · B y C: un Matcher por equipo que recorre BIO con su semilla hasta ganar Novice.
Si falta un estado necesario (A en Trained o Mature, B y C en Novice), se frena y se avisa.

Operaciones (cada una sobre agentes reconstruidos de forma determinista):
  1. colaboración A → B (axioma [b]): la «transferencia a un agente novato» del pedido;
  2. cooperación B ↔ C (axioma [a]);
  3. contraejemplos: cooperación A ↔ B (estados distintos) y colaboración B → A (hacia un
     estado superior), rechazadas con el axioma.
Se siguen T* (la primera teoría que nace en P1) y T*✓ (la primera teoría de A con U > 0,75),
con su cadena prov:wasDerivedFrom en el receptor, y el efecto en el planificador de B.

Salidas (docs/parada_tecnica/v2/): p2a.json, p2a_compartir.md, p2a_procedencia.ttl.
Uso:  python experiments/parada_tecnica/p2a_compartir.py [--out DIR]
"""
from __future__ import annotations
import argparse
import copy

from comun_pt import cargar_config, encabezado_md, guardar_json, num, out_version
from p1_teoria_punto_a_punto import construir, correr_ciclo_de_vida
from moav_hr.core.ciclo_llc import MotorLLC, NOMBRE_ESTADO
from moav_hr.core.compartir_llc import compartir
from moav_hr.core.lifecycle import MaturityState
from moav_hr.core.monitor import FairnessMonitor
from moav_hr.core.ontology.abox import theory_clave, theory_iri
from moav_hr.core.ontology.sharing_rdf import procedencia_compartida
from moav_hr.core.planificador import PlanificadorLLC
from moav_hr.core.theory import serialize, theory_key
from moav_hr.instances.hr import entorno

VERSION = "v2"


def _equipo_bio(cfg: dict, nombre: str, semilla: int):
    """Un Matcher que recorre BIO con su semilla (estado ganado)."""
    cfg_x = copy.deepcopy(cfg)
    cfg_x["semilla"] = semilla
    cfg_x, c, ag, motor, esc = construir(cfg_x, VERSION, nombre=nombre)
    res = motor.correr_capa("BIO", esc["BIO"])
    return ag, motor, res


def _agentes(cfg: dict):
    eq = cfg["compartir"]["equipos"]
    _, _, a, ma, _, ra = correr_ciclo_de_vida(cfg=copy.deepcopy(cfg), version=VERSION)
    b, mb, rb = _equipo_bio(cfg, "SemanticMatcher_B", eq["B"])
    c, mc, rc = _equipo_bio(cfg, "SemanticMatcher_C", eq["C"])
    return {"A": (a, ma, ra), "B": (b, mb, rb), "C": (c, mc, rc)}


def _decisiones(motor) -> list[dict]:
    return [{motor.cfg.attr: r["grupo"], "decision": r["accion"]} for r in motor.ciclos]


def _historia(nombre, ag, motor, res) -> dict:
    prom = [{"ciclo": e["ciclo"], "de": e["estado_antes"], "a": e["estado_despues"]}
            for e in motor.evaluaciones if e["promueve"]]
    return {"agente": ag.name, "estado": NOMBRE_ESTADO[ag.maturity.label],
            "ciclos": motor.ciclo, "teorias": len(ag.theories), "ventanas": ag.windows_observed,
            "promociones": prom}


def _seguimiento(clave_t, donante, receptor, motor_r, grafo) -> dict:
    """Dónde está la teoría en el receptor, su procedencia y qué elige el planificador."""
    t_d = next(t for t in donante.theories.theories
               if theory_key(t, donante.theories.q) == clave_t)
    t_r = next((t for t in receptor.theories.theories
                if theory_key(t, receptor.theories.q) == clave_t), None)
    iri_r = theory_iri(receptor.name, t_d, receptor.theories.q)
    deriv = [str(o) for o in grafo.objects(iri_r, None)
             if str(o).startswith(str(theory_iri(donante.name, t_d, donante.theories.q))[:20])]
    pl = PlanificadorLLC(receptor.theories, motor_r.cfg.acciones_orden, alpha=1.0,
                         **MotorLLC.parametros_validez(motor_r.cfg))
    d = pl.planificar(t_d.si, receptor.layer.value, entorno.operador_bio_matcher(t_d.si))
    return {"clave": list(clave_t), "si": t_d.si, "a": t_d.a, "sf": t_d.sf,
            "iri_donante": str(theory_iri(donante.name, t_d, donante.theories.q)),
            "iri_receptor": str(iri_r),
            "en_donante": {"p": t_d.p, "k": t_d.k, "u": round(t_d.u, 4)},
            "en_receptor": None if t_r is None else {"p": t_r.p, "k": t_r.k, "u": round(t_r.u, 4)},
            "prov_wasDerivedFrom": [str(o) for o in grafo.objects(iri_r, PROV_DERIVED)],
            "planificador_del_receptor": {
                "capa": receptor.layer.value, "accion": d.accion, "motivo": d.motivo,
                "teoria": None if d.teoria is None else d.teoria.id,
                "elige_esta_teoria": d.teoria is not None and t_r is not None and d.teoria is t_r,
                "candidatas": d.candidatas}}


def correr(out=None) -> dict:
    global PROV_DERIVED
    from moav_hr.core.ontology.ns import PROV
    PROV_DERIVED = PROV.wasDerivedFrom
    destino = out_version(out, VERSION)
    cfg = cargar_config(version=VERSION)
    comp = cfg["compartir"]
    m0, delta = comp["m0_historia_minima"], cfg["omega"]["delta"]
    ag = _agentes(cfg)
    historias = {k: _historia(k, *v) for k, v in ag.items()}
    a, ma, _ = ag["A"]
    b, mb, _ = ag["B"]
    c, mc, _ = ag["C"]
    faltan = []
    if a.maturity not in (MaturityState.TRAINED, MaturityState.MATURE):
        faltan.append(f"A está en {NOMBRE_ESTADO[a.maturity.label]}: hace falta Trained o Mature")
    for k, x in (("B", b), ("C", c)):
        if x.maturity != MaturityState.NOVATO:
            faltan.append(f"{k} está en {NOMBRE_ESTADO[x.maturity.label]}: hace falta Novice")
    salida = {"demo": "P2a — cooperación, colaboración y transferencia (E3)", "version": VERSION,
              "agentes": historias}
    if faltan:
        salida.update(detenido=True, motivo="falta un estado ganado necesario: " + "; ".join(faltan))
        guardar_json(salida, "p2a.json", destino)
        (destino / "p2a_compartir.md").write_text(_md(salida), encoding="utf-8")
        return salida

    mon = FairnessMonitor(tau=cfg["omega"]["tau"], attr=cfg["omega"]["atributo"],
                          disparity_threshold=cfg["omega"]["tau_b"])
    t_est = next(t for t in a.theories.theories if t.id == ma.ciclos[0]["teoria_registrada"])
    primer_ok = next((r for r in ma.ciclos if r["u"] > cfg["ciclo_de_vida"]["umbral_ciclo_exitoso"]),
                     None)
    t_ok = None if primer_ok is None else next(
        t for t in a.theories.theories if t.id == primer_ok["teoria_registrada"])

    # 1) colaboración A → B
    a1, ma1 = ag["A"][0], ag["A"][1]
    b1, mb1 = b, mb
    r1 = compartir("colaboracion", a1, b1, mon, {a1.name: _decisiones(ma1)}, m0, delta,
                   mb1.es_acierto)
    grafo = procedencia_compartida(b1.name, a1.name, b1.theories.theories, a1.theories.theories,
                                   actividad="colaboracion_A_B")
    (destino / "p2a_procedencia.ttl").write_text(grafo.serialize(format="turtle"),
                                                 encoding="utf-8")
    seguimiento = {"T*": _seguimiento(theory_key(t_est, a1.theories.q), a1, b1, mb1, grafo)}
    if t_ok is not None:
        seguimiento["T*✓"] = _seguimiento(theory_key(t_ok, a1.theories.q), a1, b1, mb1, grafo)
        seguimiento["T*✓"]["ciclo_en_que_supera_0_75"] = primer_ok["ciclo"]
    consulta = """PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX moacv: <https://moav-hr.diit.unlam.edu.ar/ontology/>
SELECT ?receptor ?donante WHERE { ?receptor prov:wasDerivedFrom ?donante ;
                                           moacv:clave ?c . FILTER(?c = ?clave) }"""
    cadenas = {}
    for nombre, t in (("T*", t_est), ("T*✓", t_ok)):
        if t is None:
            continue
        from rdflib import Literal
        from rdflib.namespace import XSD
        filas = grafo.query(consulta, initBindings={
            "clave": Literal(theory_clave(t, a1.theories.q), datatype=XSD.string)})
        cadenas[nombre] = [{"receptor": str(x.receptor), "donante": str(x.donante)} for x in filas]

    # 2) cooperación B ↔ C (agentes reconstruidos: B sin la colaboración anterior)
    b2, mb2, _ = _equipo_bio(cfg, "SemanticMatcher_B", comp["equipos"]["B"])
    c2, mc2, _ = _equipo_bio(cfg, "SemanticMatcher_C", comp["equipos"]["C"])
    r2 = compartir("cooperacion", b2, c2, mon, {b2.name: _decisiones(mb2),
                                               c2.name: _decisiones(mc2)}, m0, delta,
                   mb2.es_acierto)

    # 3) contraejemplos de los axiomas
    a3, ma3 = ag["A"][0], ag["A"][1]
    b3, mb3, _ = _equipo_bio(cfg, "SemanticMatcher_B", comp["equipos"]["B"])
    r3 = compartir("cooperacion", a3, b3, mon, {a3.name: _decisiones(ma3),
                                               b3.name: _decisiones(mb3)}, m0, delta)
    r4 = compartir("colaboracion", b3, a3, mon, {b3.name: _decisiones(mb3)}, m0, delta)

    salida.update(detenido=False, operaciones={
        "colaboracion_A_B": r1, "cooperacion_B_C": r2,
        "contraejemplo_cooperacion_A_B": r3, "contraejemplo_colaboracion_B_A": r4},
        seguimiento=seguimiento, consulta_sparql=consulta, cadenas_prov=cadenas,
        archivos=["p2a.json", "p2a_compartir.md", "p2a_procedencia.ttl"])
    guardar_json(salida, "p2a.json", destino)
    (destino / "p2a_compartir.md").write_text(_md(salida), encoding="utf-8")
    return salida


def _op_md(nombre, r) -> list[str]:
    L = [f"### {nombre}", "",
         f"- **Estados:** donante {NOMBRE_ESTADO.get(r['estados']['donante'], r['estados']['donante'])}, "
         f"receptor {NOMBRE_ESTADO.get(r['estados']['receptor'], r['estados']['receptor'])}."]
    for ag, o in r["omega"].items():
        ev = o["evidencia_sesgo"]
        vent = f"{o['ventanas']} ventana" + ("" if o["ventanas"] == 1 else "s")
        L.append(f"- **Ω sobre {ag}:** can_donate = {o['can_donate']} ({vent}); "
                 f"brecha {('—' if ev['brecha'] is None else num(ev['brecha'], 3))}, LCB "
                 f"{('—' if ev['lcb'] is None else num(ev['lcb'], 3))} frente a τ_b = "
                 f"{num(ev['tau_b'], 3)} → {ev['motivo']}; r informada "
                 f"{num(o['reputacion_informada'], 3)}.")
    L.append(f"- **Resultado:** {'aceptada' if r['aceptada'] else 'rechazada'} — {r['motivo']}"
             + (f". Axioma: {r['axioma']}" if r.get("axioma") else "") + ".")
    if r["aceptada"]:
        L += [f"- **Base del receptor:** {r['base_receptor_antes']} → {r['base_receptor_despues']} "
              f"teorías; igual {r['conteo']['igual']} · similar {r['conteo']['similar']} · nueva "
              f"{r['conteo']['nueva']}; ΣP = K en el receptor: "
              f"{'se cumple' if r['invariante_receptor'] else 'NO'}.", "",
              "| Teoría del donante (Si · A · Sf) | Entra como | En el donante (P, K, U) | "
              "En el receptor antes | En el receptor después |", "|---|---|---|---|---|"]
        for f in r["teorias"]:
            pk = lambda d: "—" if d is None else f"{d['p']}, {d['k']}, {num(d['u'], 3)}"  # noqa: E731
            L.append(f"| {f['clave'][0]} · {f['clave'][1]} · {f['clave'][2]} | {f['categoria']} | "
                     f"{pk(f['en_donante'])} | {pk(f['en_receptor_antes'])} | "
                     f"{pk(f['en_receptor_despues'])} |")
    return L + [""]


def _md(s) -> str:
    L = encabezado_md("P2a · Cooperación, colaboración y transferencia (pre-registro v2)")
    L += ["## Agentes (estados ganados)", "", "| Equipo | Agente | Estado | Ciclos | Teorías | "
          "Ventanas | Promociones |", "|---|---|---|---|---|---|---|"]
    for k, h in s["agentes"].items():
        L.append(f"| {k} | {h['agente']} | {h['estado']} | {h['ciclos']} | {h['teorias']} | "
                 f"{h['ventanas']} | " + ("; ".join(f"ciclo {p['ciclo']}: {p['de']} → {p['a']}"
                                                   for p in h["promociones"]) or "—") + " |")
    L.append("")
    if s.get("detenido"):
        L += ["## Detenido", "", f"**{s['motivo']}.** Según E2_RESPUESTA §4, no se fijan estados "
              "a mano: se frena y se avisa.", ""]
        return "\n".join(L)
    op = s["operaciones"]
    L += ["## Operaciones", ""]
    L += _op_md("1. Colaboración A → B (transferencia a un agente novato)", op["colaboracion_A_B"])
    L += _op_md("2. Cooperación B ↔ C", op["cooperacion_B_C"])
    L += _op_md("3a. Contraejemplo: cooperación A ↔ B", op["contraejemplo_cooperacion_A_B"])
    L += _op_md("3b. Contraejemplo: colaboración B → A", op["contraejemplo_colaboracion_B_A"])
    L += ["## T\\* y T\\*✓ en el receptor (después de la colaboración A → B)", ""]
    for nombre, seg in s["seguimiento"].items():
        p = seg["planificador_del_receptor"]
        L += [f"### {nombre.replace('*', chr(92) + '*')}: {seg['clave'][0]} · {seg['clave'][1]} · {seg['clave'][2]}", "",
              f"- **En A (donante):** P = {seg['en_donante']['p']}, K = {seg['en_donante']['k']}, "
              f"U = {num(seg['en_donante']['u'], 3)}"
              + (f"; supera U = 0,75 en el ciclo {seg['ciclo_en_que_supera_0_75']} de P1"
                 if "ciclo_en_que_supera_0_75" in seg else "") + ".",
              "- **En B (receptor):** " + ("no está" if seg["en_receptor"] is None else
                                          f"P = {seg['en_receptor']['p']}, K = {seg['en_receptor']['k']}, "
                                          f"U = {num(seg['en_receptor']['u'], 3)}") + ".",
              f"- **Procedencia:** `{seg['iri_receptor']}` prov:wasDerivedFrom "
              + (", ".join(f"`{x}`" for x in seg["prov_wasDerivedFrom"]) or "—") + ".",
              f"- **Planificador de B** (capa {p['capa']}) ante un caso con esa Si: elige "
              f"{p['accion']} ({p['motivo']}" + (f", T{p['teoria']}" if p["teoria"] else "")
              + f"); ¿es esta teoría? **{'sí' if p['elige_esta_teoria'] else 'no'}**.", ""]
    L += ["## Consulta SPARQL de la cadena de procedencia", "", "```sparql",
          s["consulta_sparql"], "```", ""]
    for nombre, filas in s["cadenas_prov"].items():
        L.append(f"- **{nombre.replace('*', chr(92) + '*')}:** " + ("; ".join(f"{f['receptor']} ← {f['donante']}" for f in filas)
                                       or "sin resultados") + ".")
    return "\n".join(L) + "\n"


PROV_DERIVED = None

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="P2a — compartición (E3)")
    ap.add_argument("--out", default=None)
    s = correr(ap.parse_args().out)
    if s.get("detenido"):
        print("P2a DETENIDO:", s["motivo"])
    else:
        op = s["operaciones"]
        print("P2a · " + " · ".join(f"{k}: {'aceptada' if v['aceptada'] else 'rechazada'}"
                                    for k, v in op.items()))
        print({k: (v["agente"], v["estado"], v["ventanas"]) for k, v in s["agentes"].items()})
