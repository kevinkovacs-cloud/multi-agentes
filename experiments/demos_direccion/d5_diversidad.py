#!/usr/bin/env python
"""
D5 — Diversidad en comité con sesgos PROGRAMADOS (ítem I5, pedido de Ierache del 26/06).

Tres comités de k = 3 miembros (core/committee.Committee, agregación por media) puntúan a
los MISMOS candidatos. Cada miembro es un MOACVAgent cuyo score es la calificación real
más un sesgo programado (mismo espíritu que las etapas-juguete de e0_instrumento.py):

    score_i(c) = true_qual(c) + b_i(c),   z(c) = 1 si c es del grupo no-AR, 0 si AR

  (a) homogéneo: los tres penalizan al grupo no-AR igual (−β·z) y el ruido es casi todo
      común → series de sesgo muy correlacionadas;
  (b) diverso: los sesgos de grupo van en direcciones distintas (−β·z, +β·z, 0) y el
      ruido es independiente → series descorrelacionadas o anticorrelacionadas;
  (c) diverso con componente compartida: (b) más un piso común −φ·z para los tres.

Para cada comité: D(M) = (1 − ρ̄)/2 sobre las series de sesgo por miembro
(Committee.member_bias_series → fairness.diversity), d_max(3), la disparidad Δ_DP de cada
miembro y la del comité, y la relación comité/miembro.

PARÁMETROS PROGRAMADOS: ilustra el mecanismo de la condición C2 (diversidad); NO es
evidencia de la conjetura de atenuación.

Uso:  python experiments/demos_direccion/d5_diversidad.py [--out DIR]
"""
from __future__ import annotations
import argparse

import numpy as np

from comun import (ATTR, C_AZUL, C_ROJO, C_TEXTO, C_VERDE, C_VIOLETA, CRITERIO, UMBRAL,
                   comas, estilo_figuras, guardar_figura, guardar_json, num, out_dir,
                   pie_rotulos, plt)
from moav_hr.core import fairness
from moav_hr.core.agent import MOACVAgent
from moav_hr.core.audit.trail import AuditTrail
from moav_hr.core.committee import Committee
from moav_hr.instances.hr.synthetic import Candidate

ROTULO_D5 = ("parámetros programados: ilustra el mecanismo de la condición C2 (diversidad); "
             "no es evidencia de la conjetura de atenuación")

# parámetros PROGRAMADOS (entradas de diseño, no resultados)
SEMILLA = 20260929
N_POR_GRUPO = 200
TQ_RANGO = (0.60, 0.95)      # calificación real, misma distribución en ambos grupos
BETA = 0.10                  # sesgo de grupo de cada miembro
PISO = 0.08                  # componente de sesgo compartida (comité c)
SIGMA = 0.03                 # ruido por candidato
SIGMA_HOMOG_IND = 0.005      # ruido individual residual del comité homogéneo
K = 3
ORIGENES_NO_AR = ("BR", "CL", "CO", "SY", "IN", "EG")


class MiembroProgramado(MOACVAgent):
    """Miembro de comité con sesgo programado: score = true_qual + sesgo[id]."""

    def __init__(self, nombre: str, sesgo: dict[int, float]):
        super().__init__(nombre, "matcher")
        self.sesgo = sesgo

    def run(self, state: dict) -> dict:
        c = state["candidate"]
        state["matcher"] = {"score": round(c.true_qual + self.sesgo[c.id], 4),
                            "source": "programado", "n_retrieved": 0, "si": {}}
        return state


def poblacion():
    rng = np.random.default_rng(SEMILLA)
    n = 2 * N_POR_GRUPO
    tq = rng.uniform(*TQ_RANGO, size=n)
    cands = []
    for i in range(n):
        no_ar = i % 2 == 1
        cands.append(Candidate(
            id=i + 1, name=f"C-{i + 1:03d}", gender="F" if i % 4 < 2 else "M", age=30,
            origin=ORIGENES_NO_AR[(i // 2) % len(ORIGENES_NO_AR)] if no_ar else "AR",
            exp=5, edu="Licenciatura", skills=("Python",), match_score=round(float(tq[i]), 4),
            bias_risk="low", true_qual=round(float(tq[i]), 4)))
    z = np.array([1.0 if c.origin_group == "no-AR" else 0.0 for c in cands])
    comun = rng.normal(0.0, 1.0, size=n)
    indiv = rng.normal(0.0, 1.0, size=(K, n))
    return cands, z, comun, indiv


def sesgos(config: str, z, comun, indiv) -> list[np.ndarray]:
    if config == "homogeneo":
        return [-BETA * z + SIGMA * comun + SIGMA_HOMOG_IND * indiv[i] for i in range(K)]
    direcciones = (-1.0, +1.0, 0.0)
    b = [d * BETA * z + SIGMA * indiv[i] for i, d in enumerate(direcciones)]
    if config == "diverso":
        return b
    if config == "diverso_con_piso":
        return [bi - PISO * z for bi in b]
    raise ValueError(config)


DESCRIPCION = {
    "homogeneo": "(a) homogéneo: los tres miembros penalizan al grupo no-AR con −β·z y el "
                 "ruido es casi todo común",
    "diverso": "(b) diverso: sesgos de grupo en direcciones distintas (−β·z, +β·z, 0) y "
               "ruido independiente",
    "diverso_con_piso": "(c) diverso con componente compartida: (b) más un piso común −φ·z",
}


def evaluar(config: str, cands, z, comun, indiv) -> dict:
    bs = sesgos(config, z, comun, indiv)
    miembros = [MiembroProgramado(f"M{i + 1}", {c.id: float(b[j]) for j, c in enumerate(cands)})
                for i, b in enumerate(bs)]
    comite = Committee(miembros, aggregation="mean", decision_threshold=UMBRAL)
    trail = AuditTrail(f"TRC-D5-{config.upper()}")
    states = [comite.run({"candidate": c, "trail": trail}) for c in cands]
    series = comite.member_bias_series(states)
    D = fairness.diversity(series)

    def registros(scores):
        return [{"origin_group": c.origin_group, "true_qual": c.true_qual,
                 "decision": "ADVANCE" if s >= UMBRAL else "REJECT"}
                for c, s in zip(cands, scores)]

    disp_m, firm_m = [], []
    for i in range(K):
        r = registros([st["matcher"]["member_scores"][i] for st in states])
        disp_m.append(abs(fairness.disparity(r, ATTR, CRITERIO)))
        firm_m.append(fairness.disparity_signed(r, ATTR, CRITERIO, "AR"))
    rc = registros([st["matcher"]["score"] for st in states])
    disp_c = abs(fairness.disparity(rc, ATTR, CRITERIO))
    media = float(np.mean(disp_m))
    return {
        "descripcion": DESCRIPCION[config],
        "D": D, "d_max": fairness.d_max(K), "rho_medio": round(1 - 2 * D, 4),
        "disparidad_miembros": disp_m,
        "disparidad_miembros_firmada_ref_AR": firm_m,
        "disparidad_comite": disp_c,
        "disparidad_comite_firmada_ref_AR": fairness.disparity_signed(rc, ATTR, CRITERIO, "AR"),
        "media_disparidad_miembros": round(media, 4),
        "relacion_comite_sobre_media_miembros": round(disp_c / media, 4) if media else None,
        "relacion_comite_sobre_max_miembro": (round(disp_c / max(disp_m), 4)
                                              if max(disp_m) else None),
    }


def _figura(res, disp_real, destino):
    configs = list(res)
    etiquetas = {"homogeneo": "(a) homogéneo", "diverso": "(b) diverso",
                 "diverso_con_piso": "(c) diverso\ncon piso común"}
    fig = plt.figure(figsize=(9, 7.6))
    a1 = fig.add_axes([0.09, 0.33, 0.55, 0.52])
    a2 = fig.add_axes([0.75, 0.33, 0.23, 0.52])
    x = np.arange(len(configs))
    w = 0.19
    tonos = [C_AZUL, "#2E5A8A", "#4A6FA0"]
    for i in range(K):
        a1.bar(x + (i - 1.5) * w, [res[c]["disparidad_miembros"][i] for c in configs], width=w,
               color=tonos[i], edgecolor=C_TEXTO, lw=0.6,
               label="miembros M1–M3" if i == 0 else None)
    a1.bar(x + 1.5 * w, [res[c]["disparidad_comite"] for c in configs], width=w,
           color=C_ROJO, edgecolor=C_TEXTO, lw=0.6, label="comité (media)")
    for j, c in enumerate(configs):
        a1.annotate(f"comité/media = {num(res[c]['relacion_comite_sobre_media_miembros'], 2)}",
                    (x[j], max(res[c]["disparidad_miembros"] + [res[c]["disparidad_comite"]])),
                    xytext=(0, 8), textcoords="offset points", ha="center", fontsize=12,
                    color=C_TEXTO)
    a1.axhline(disp_real, color=C_VERDE, lw=2, ls=":", label="Δ de la calificación real")
    a1.set_xticks(x, [etiquetas[c] for c in configs])
    a1.set_ylabel("|Δ_DP| entre grupos (AR vs no-AR)")
    top = max(max(r["disparidad_miembros"]) for r in res.values())
    a1.set_ylim(0, top * 1.3)
    a1.legend(loc="upper left", bbox_to_anchor=(0, 1.14), ncol=3, frameon=False, fontsize=12,
              columnspacing=1.0, handlelength=1.4)
    comas(a1)
    a1.set_xticks(x, [etiquetas[c] for c in configs])
    a2.bar(x, [res[c]["D"] for c in configs], width=0.76, color=C_VIOLETA)
    dmax = res[configs[0]]["d_max"]
    a2.axhline(dmax, color=C_ROJO, lw=2, ls="--")
    a2.annotate(f"d_max(3) = {num(dmax, 2)}", (x[0] - 0.35, dmax), xytext=(0, 4),
                textcoords="offset points", ha="left", fontsize=12, color=C_ROJO)
    a2.axhline(0.5, color=C_TEXTO, lw=1.4, ls=":")
    for j, c in enumerate(configs):
        dentro = res[c]["D"] > 0.15                   # etiqueta dentro de la barra si entra
        a2.annotate(num(res[c]["D"], 3), (x[j], res[c]["D"]),
                    xytext=(0, -18 if dentro else 4), textcoords="offset points",
                    ha="center", fontsize=12, color="white" if dentro else C_TEXTO,
                    )
    a2.set_xticks(x, ["(a)", "(b)", "(c)"])
    a2.set_ylim(0, 0.9)
    a2.set_title("D(M) = (1 − ρ̄)/2", fontsize=12)
    comas(a2)
    a2.set_xticks(x, ["(a)", "(b)", "(c)"])
    fig.suptitle("D5 · Diversidad en un comité de k = 3 con sesgos programados (condición C2)",
                 x=0.012, ha="left", y=0.975, fontsize=14)
    pie_rotulos(fig, [
        ROTULO_D5[0].upper() + ROTULO_D5[1:] + ".",
        f"{2 * N_POR_GRUPO} candidatos ({N_POR_GRUPO} por grupo), misma distribución de "
        f"calificación real; score = calificación + sesgo; decisión: score ≥ {num(UMBRAL, 2)}; "
        f"β = {num(BETA, 2)}, φ = {num(PISO, 2)}, σ = {num(SIGMA, 2)}. Panel derecho: "
        "punteada en D = 0,5 (series independientes); d_max(3) es la cota de alcanzabilidad."],
        ancho=98)
    return guardar_figura(fig, "d5_diversidad.png", destino)


def correr(out=None) -> dict:
    destino = out_dir(out)
    estilo_figuras()
    cands, z, comun, indiv = poblacion()
    res = {c: evaluar(c, cands, z, comun, indiv)
           for c in ("homogeneo", "diverso", "diverso_con_piso")}
    reales = [{"origin_group": c.origin_group, "true_qual": c.true_qual,
               "decision": "ADVANCE" if c.true_qual >= UMBRAL else "REJECT"} for c in cands]
    disp_real = abs(fairness.disparity(reales, ATTR, CRITERIO))
    figura = _figura(res, disp_real, destino)
    salida = {
        "demo": "D5 — diversidad en comité con sesgos programados (I5)",
        "rotulo_obligatorio": ROTULO_D5,
        "parametros_programados": {
            "semilla": SEMILLA, "candidatos_por_grupo": N_POR_GRUPO,
            "true_qual_uniforme": list(TQ_RANGO), "beta": BETA, "piso_phi": PISO,
            "sigma": SIGMA, "sigma_individual_homogeneo": SIGMA_HOMOG_IND, "k": K,
            "agregacion": "mean", "umbral_decision": UMBRAL, "criterio": CRITERIO,
            "atributo": ATTR},
        "disparidad_de_la_calificacion_real": disp_real,
        "comites": res,
        "figuras": [figura.name],
    }
    guardar_json(salida, "d5_diversidad.json", destino)
    return salida


def main() -> None:
    ap = argparse.ArgumentParser(description="D5 — diversidad en comité")
    ap.add_argument("--out", default=None, help="carpeta de salida (default docs/demos_direccion)")
    s = correr(ap.parse_args().out)
    for c, r in s["comites"].items():
        print(f"D5 · {c}: D={r['D']} (d_max={r['d_max']}) · miembros={r['disparidad_miembros']} "
              f"· comité={r['disparidad_comite']} · comité/media={r['relacion_comite_sobre_media_miembros']}")


if __name__ == "__main__":
    main()
