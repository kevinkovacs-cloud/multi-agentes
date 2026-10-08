#!/usr/bin/env python
"""
P2b — Cómo se rankea y se recupera la teoría generada antes por el propio agente
(punto 2b del pedido; Bloque E · E2.8).

El mismo agente de P1 (la corrida es determinista: se reconstruye con
`correr_ciclo_de_vida`), más adelante:
  (i)   un caso con la misma Si que T*: candidatas de la celda ordenadas por (U, P, K)
        (Fig. 4.21), la elegida y por qué;
  (ii)  un caso con una Si nueva (celda vacía): respaldo por similitud, extensión declarada
        (DE-2), que en P1 estaba desactivado;
  (iii) un caso sin nada aplicable: «azar» del planificador (en BIO y TBO, la primera acción
        no probada; en WIO, el operador BIO).
Para (i) y para todas las celdas de la base se compara α = 1 con α = 0,5 (DE-5).

Salidas: docs/parada_tecnica/p2b_planificador.md y p2b.json.
Uso:  python experiments/parada_tecnica/p2b_planificador.py [--out DIR]
"""
from __future__ import annotations
import argparse
import itertools

from comun_pt import encabezado_md, guardar_json, num, out_dir
from p1_teoria_punto_a_punto import correr_ciclo_de_vida
from moav_hr.core.planificador import PlanificadorLLC
from moav_hr.core.retrieval import similarity
from moav_hr.core.theory import serialize, theory_key
from moav_hr.instances.hr import entorno
from moav_hr.instances.hr.roles_llc import RolMatcherLLC

EDUS = ("Licenciatura", "Maestría", "Doctorado", "Especialización")
BANDAS = ("junior", "mid", "senior")


def _todas_las_si() -> list[dict]:
    return [{"skills_match": s, "exp_band": b, "edu": e, "seniority_ok": b != "junior"}
            for e, b, s in itertools.product(EDUS, BANDAS, range(4))]


def _lecturas(motor, t) -> dict:
    lec = motor.registro_e.lecturas(theory_key(t, motor.agente.theories.q))
    por = {}
    for g, ok in lec:
        por.setdefault(g, [0, 0])
        por[g][0] += 1
        por[g][1] += ok
    return {g: {"usos": v[0], "aciertos": v[1]} for g, v in sorted(por.items())}


def _decision(d) -> dict:
    return {"accion": d.accion, "motivo": d.motivo, "es_azar": d.es_azar,
            "teoria": None if d.teoria is None else d.teoria.id,
            "validez_aplicada": d.validez_aplicada, "desacuerdo_alg47": d.desacuerdo_alg47,
            "equidad_usada": d.equidad_usada, "candidatas": d.candidatas}


def correr(out=None) -> dict:
    destino = out_dir(out)
    cfg, c, agente, motor, esc, res = correr_ciclo_de_vida()
    rol = RolMatcherLLC(cfg["entorno"]["ruido_wio_epsilon"], cfg["semilla"])
    capa = agente.layer.value
    base = agente.theories
    t_est = next(t for t in base.theories if t.id == motor.ciclos[0]["teoria_registrada"])
    pl1 = PlanificadorLLC(base, c.acciones_orden, alpha=1.0, registro_e=motor.registro_e,
                          m_min=c.m_min)
    pl05 = PlanificadorLLC(base, c.acciones_orden, alpha=cfg["utilidad"]["alpha_comparacion"],
                           registro_e=motor.registro_e, m_min=c.m_min)
    pl_sim = PlanificadorLLC(base, c.acciones_orden, respaldo_similitud=True,
                             delta=c.delta, alpha=1.0)

    # (i) la misma Si que T*
    caso_i = entorno.caso_con_si(t_est.si, 1, semilla=cfg["semilla"])
    si_i = rol.percibir(caso_i)
    bio_i = rol.accion_bio(si_i, caso_i)
    d_i, d_i05 = pl1.planificar(si_i, capa, bio_i), pl05.planificar(si_i, capa, bio_i)
    lecturas_i = {t.id: _lecturas(motor, t) for t in base.applicable(si_i)}

    # celdas vacías: con respaldo por similitud (ii) y sin nada aplicable (iii)
    vacias = [si for si in _todas_las_si() if not base.applicable(si)]
    def max_sim(si):
        return max((similarity(si, t.si) for t in base.theories if t.u > 0), default=0.0)
    con_sim = [si for si in vacias if max_sim(si) >= c.delta]
    sin_nada = [si for si in vacias if max((similarity(si, t.si) for t in base.theories),
                                           default=0.0) < c.delta]
    caso_ii = entorno.caso_con_si(con_sim[0], 2, semilla=cfg["semilla"]) if con_sim else None
    caso_iii = entorno.caso_con_si(sin_nada[0], 3, semilla=cfg["semilla"]) if sin_nada else None
    ii = iii = None
    if caso_ii is not None:
        si = rol.percibir(caso_ii)
        d = pl_sim.planificar(si, capa, rol.accion_bio(si, caso_ii))
        ii = {"si": si, "similitud_maxima": round(max_sim(si), 4), "con_respaldo": _decision(d),
              "sin_respaldo_como_en_p1": _decision(pl1.planificar(si, capa,
                                                                  rol.accion_bio(si, caso_ii)))}
    if caso_iii is not None:
        si = rol.percibir(caso_iii)
        bio = rol.accion_bio(si, caso_iii)
        iii = {"si": si, "accion_bio": bio,
               "similitud_maxima": round(max((similarity(si, t.si) for t in base.theories),
                                             default=0.0), 4),
               "en_la_capa_del_agente": {"capa": capa, **_decision(pl_sim.planificar(si, capa, bio))},
               "en_wio": _decision(pl_sim.planificar(si, "WIO", bio))}

    # α = 1 frente a α = 0,5 en todas las celdas de la base
    celdas = {serialize(t.si): t.si for t in base.theories}
    cambios, con_e = [], 0
    for si in celdas.values():
        a1 = pl1.planificar(si, capa, entorno.operador_bio_matcher(si))
        a05 = pl05.planificar(si, capa, entorno.operador_bio_matcher(si))
        con_e += a05.equidad_usada
        if (a1.accion, a1.teoria and a1.teoria.id) != (a05.accion, a05.teoria and a05.teoria.id):
            cambios.append({"si": si, "alpha_1": _decision(a1), "alpha_05": _decision(a05)})

    salida = {
        "demo": "P2b — ranking y recuperación de la teoría propia",
        "agente": {"estado": res["estado_final"], "capa": capa, "teorias": len(base),
                   "ciclos": res["ciclos"]},
        "teoria_estrella": {"id": t_est.id, "si": t_est.si, "a": t_est.a, "sf": t_est.sf,
                            "p": t_est.p, "k": t_est.k, "u": t_est.u},
        "caso_i_misma_si": {"si": si_i, "si_igual_a_t_estrella": si_i == t_est.si,
                            "accion_bio": bio_i, "alpha_1": _decision(d_i),
                            "alpha_05": _decision(d_i05), "e_t_por_candidata": lecturas_i,
                            "alpha_cambia_la_elegida": (d_i.accion, d_i.teoria and d_i.teoria.id)
                            != (d_i05.accion, d_i05.teoria and d_i05.teoria.id)},
        "caso_ii_si_nueva_con_similitud": ii,
        "caso_iii_sin_nada_aplicable": iii,
        "alpha_en_todas_las_celdas": {"celdas": len(celdas), "celdas_con_e_estimable": con_e,
                                      "m_min_por_grupo": c.m_min, "cambios": cambios},
    }
    guardar_json(salida, "p2b.json", destino)
    (destino / "p2b_planificador.md").write_text(_md(salida, c), encoding="utf-8")
    return salida


def _tabla(cands, extra=False) -> list[str]:
    cab = "| Puesto | Teoría | A | Sf | u_tarea | U para ordenar | P | K |" + (
        " Similitud |" if extra else "")
    L = [cab, "|" + "---|" * (8 + extra)]
    for f in cands:
        L.append(f"| {f['puesto']} | T{f['id']} | {f['a']} | {serialize(f['sf'])} | "
                 f"{num(f['u_tarea'], 2)} | {num(f['u_orden'], 3)} | {f['p']} | {f['k']} |"
                 + (f" {num(f['similitud'], 3)} |" if extra else ""))
    return L


def _por_que(d) -> str:
    return {"celda": "es la primera del orden (U, P, K) en la celda y su u_tarea > 0",
            "similitud": "la celda está vacía y es la primera, en el orden (U, P, K), entre las "
                         "teorías con similitud ≥ δ y u_tarea > 0 (extensión declarada)",
            "azar_no_probada": "no hay plan válido: «azar» del planificador, primera acción no "
                               "probada en la celda (orden fijo)",
            "azar_bio": "no hay plan válido: «azar» del planificador con el operador BIO"}[d["motivo"]]


def _md(s, c) -> str:
    L = encabezado_md("P2b · Ranking y recuperación de la teoría propia")
    a = s["agente"]
    t = s["teoria_estrella"]
    L += [f"**Agente:** el de P1 al terminar su corrida: estado {a['estado']}, capa {a['capa']}, "
          f"{a['teorias']} teorías, {a['ciclos']} ciclos.", "",
          f"**T\\*:** T{t['id']} · Si {serialize(t['si'])} · A = {t['a']} · Sf = "
          f"{serialize(t['sf'])} · P = {t['p']}, K = {t['k']}, U = {num(t['u'], 2)}.", "",
          "## (i) Un caso con la misma Si que T*", ""]
    ci = s["caso_i_misma_si"]
    L += _tabla(ci["alpha_1"]["candidatas"])
    d = ci["alpha_1"]
    L += ["", f"**Elegida (α = 1):** {d['accion']}"
          + (f" (T{d['teoria']})" if d["teoria"] else "") + f". Por qué: {_por_que(d)}.",
          f"Regla de validez aplicada: {'sí' if d['validez_aplicada'] else 'no'}. "
          f"Desacuerdo Fig. 4.21 / Alg. 4.7: "
          f"{'sí, ' + serialize(d['desacuerdo_alg47']) if d['desacuerdo_alg47'] else 'no'}.", "",
          "**E(t) de cada candidata** (plano de auditoría; decisiones en las que fue el plan): "
          + ("; ".join(f"T{tid}: {serialize(v) if v else 'sin usos como plan'}"
                       for tid, v in ci["e_t_por_candidata"].items())) + ".", "",
          f"**α = 0,5:** elige {ci['alpha_05']['accion']}"
          + (f" (T{ci['alpha_05']['teoria']})" if ci["alpha_05"]["teoria"] else "")
          + f"; ¿cambia la elegida? **{'sí' if ci['alpha_cambia_la_elegida'] else 'no'}**. "
          + ("Ninguna candidata tiene ê(t) estimable con m_min = "
             f"{c.m_min} usos por grupo: se usa α = 1 y queda registrado."
             if not ci["alpha_05"]["equidad_usada"] else "Al menos una candidata tiene ê(t)."),
          ""]
    ii = s["caso_ii_si_nueva_con_similitud"]
    L += ["## (ii) Un caso con una Si nueva: respaldo por similitud (extensión declarada)", ""]
    if ii is None:
        L.append("No hay una Si sin celda con alguna teoría a similitud ≥ δ: no se pudo mostrar.")
    else:
        d = ii["con_respaldo"]
        L += [f"Si {serialize(ii['si'])} (celda vacía; similitud máxima con una teoría de "
              f"u_tarea > 0 = {num(ii['similitud_maxima'], 3)}; δ = {num(c.delta, 1)}).", ""]
        L += _tabla(d["candidatas"], extra=True)
        L += ["", f"**Elegida con el respaldo activado:** {d['accion']}"
              + (f" (T{d['teoria']})" if d["teoria"] else "") + f". Por qué: {_por_que(d)}.",
              f"**Como en P1 (respaldo desactivado):** {ii['sin_respaldo_como_en_p1']['accion']} "
              f"— {_por_que(ii['sin_respaldo_como_en_p1'])}.", ""]
    iii = s["caso_iii_sin_nada_aplicable"]
    L += ["## (iii) Un caso sin nada aplicable", ""]
    if iii is None:
        L.append("No hay una Si sin celda y sin teorías a similitud ≥ δ: no se pudo mostrar.")
    else:
        e, w = iii["en_la_capa_del_agente"], iii["en_wio"]
        L += [f"Si {serialize(iii['si'])} (celda vacía; similitud máxima "
              f"{num(iii['similitud_maxima'], 3)} < δ; acción del operador BIO = "
              f"{iii['accion_bio']}).", "",
              f"- **En la capa del agente ({e['capa']}):** {e['accion']} — {_por_que(e)}; "
              f"cuenta como azar: {'sí' if e['es_azar'] else 'no'}.",
              f"- **Si el agente estuviera en WIO:** {w['accion']} — {_por_que(w)}; cuenta como "
              f"azar: {'sí' if w['es_azar'] else 'no'}.", ""]
    al = s["alpha_en_todas_las_celdas"]
    L += ["## α = 1 frente a α = 0,5 en todas las celdas de la base", "",
          f"Celdas: {al['celdas']}; con ê(t) estimable en alguna candidata (m_min = "
          f"{al['m_min_por_grupo']} usos por grupo): {al['celdas_con_e_estimable']}; celdas donde "
          f"α = 0,5 cambia la elegida: **{len(al['cambios'])}**.", ""]
    for ch in al["cambios"]:
        L.append(f"- Si {serialize(ch['si'])}: α = 1 → {ch['alpha_1']['accion']}, α = 0,5 → "
                 f"{ch['alpha_05']['accion']}.")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="P2b — planificador")
    ap.add_argument("--out", default=None)
    s = correr(ap.parse_args().out)
    ci = s["caso_i_misma_si"]
    print(f"P2b · (i) elige {ci['alpha_1']['accion']} ({ci['alpha_1']['motivo']}), α=0,5 cambia: "
          f"{ci['alpha_cambia_la_elegida']} · (ii) "
          f"{s['caso_ii_si_nueva_con_similitud'] and s['caso_ii_si_nueva_con_similitud']['con_respaldo']['motivo']}"
          f" · (iii) {s['caso_iii_sin_nada_aplicable'] and s['caso_iii_sin_nada_aplicable']['en_la_capa_del_agente']['motivo']}"
          f" · cambios por α en la base: {len(s['alpha_en_todas_las_celdas']['cambios'])}")
