#!/usr/bin/env python
"""
D1 — Selección de teoría por embeddings, con el espacio vectorial (pedido P3 de Ierache).

Base: la del Semantic Matcher después del lote de la PoC (pipeline.warmup sobre los 12
candidatos, igual que run_poc.py). Consulta: la Si de Fátima (caso 3). Se calcula la
similitud consulta–teoría con embeddings (MOAV_SIMILARITY=embeddings, el backend de
core/retrieval.py) y con token-cosine (default), se marcan las que superan el δ que usa
REALMENTE el Matcher y se ordena con la clave de TheoryRetriever.retrieve.

Si el modelo de embeddings no está disponible (extra no instalado o sin red), el demo
corre solo con token-cosine, deja la figura de barras y registra el fallo en el JSON.

Uso:  python experiments/demos_direccion/d1_embeddings.py [--backend auto|token-cosine]
                                                          [--out DIR]
"""
from __future__ import annotations
import argparse
import inspect
import os

import numpy as np

from comun import (C_AZUL, C_ROJO, C_TEXTO, C_VERDE, backend_similitud, estilo_figuras,
                   comas, guardar_figura, guardar_json, num, out_dir, pie_rotulos, plt)
from moav_hr.core import retrieval
from moav_hr.core.agent import MOACVAgent
from moav_hr.core.retrieval import TheoryRetriever, similarity
from moav_hr.core.theory import serialize
from moav_hr.instances.hr.parser_agent import build_si, normalize_profile
from moav_hr.instances.hr.pipeline import HRPipeline
from moav_hr.instances.hr.synthetic import CANDIDATES, get

CASO_CONSULTA = 3          # Fátima Al-Hassan
MODELO_DEFAULT = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def _evaluar(matcher, teorias, q, backend: str) -> dict:
    """Similitudes, filtro por δ y orden con el código real de recuperación."""
    with backend_similitud(backend):
        sims = [similarity(q, t.si) for t in teorias]
        todas = TheoryRetriever(matcher.theories, delta=matcher.retriever.delta,
                                top_k=len(teorias)).retrieve(q)
        top = matcher.retrieve(q)                       # el retriever del Matcher (top-k)
    return {"sims": sims, "ranking": [t.id for t in todas], "top": [t.id for t in top]}


def _resumen(ev: dict, teorias, delta: float) -> dict:
    ids = [t.id for t in teorias]
    return {
        "superan_delta": [i for i, s in zip(ids, ev["sims"]) if s >= delta],
        "ranking_entre_las_que_superan_delta": ev["ranking"],
        "recuperadas_top_k": ev["top"],
        "seleccionada": ev["top"][0] if ev["top"] else None,
        "similitud_min": round(min(ev["sims"]), 4),
        "similitud_max": round(max(ev["sims"]), 4),
    }


def _etiquetar(ax, fig, xs, ys, textos) -> None:
    """Coloca cada etiqueta en el primer desplazamiento que no se superpone con otra
    etiqueta ni con un punto (legibilidad: crítica de Becerra)."""
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    ocupadas = []
    from matplotlib.transforms import Bbox
    for x, y in zip(xs, ys):
        px, py = ax.transData.transform((x, y))
        ocupadas.append(Bbox.from_extents(px - 9, py - 9, px + 9, py + 9))
    desplaz = [(12, 12), (12, -14), (-12, 12), (-12, -14), (16, 0), (-16, 0),
               (0, 22), (0, -24), (26, 30), (26, -32), (-26, 30), (-26, -32),
               (40, 0), (-40, 0), (0, 40), (0, -42)]
    ax_bb = ax.get_window_extent(rend)
    for x, y, txt in zip(xs, ys, textos):
        elegido = None
        for dx, dy in desplaz:
            ann = ax.annotate(txt, (x, y), xytext=(dx, dy), textcoords="offset points",
                              ha="left" if dx >= 0 else "right", va="center",
                              fontsize=12, color=C_TEXTO,
                              arrowprops=dict(arrowstyle="-", color=C_TEXTO, lw=0.8))
            bb = ann.get_window_extent(rend).expanded(1.04, 1.12)
            dentro = (bb.x0 >= ax_bb.x0 and bb.x1 <= ax_bb.x1
                      and bb.y0 >= ax_bb.y0 and bb.y1 <= ax_bb.y1)
            if dentro and not any(bb.overlaps(o) for o in ocupadas):
                elegido = (ann, bb)
                break
            ann.remove()
        if elegido is None:                           # sin lugar libre: primer desplazamiento
            ann = ax.annotate(txt, (x, y), xytext=desplaz[0], textcoords="offset points",
                              ha="left", va="center", fontsize=12, color=C_TEXTO)
            elegido = (ann, ann.get_window_extent(rend))
        ocupadas.append(elegido[1])


def _figura_pca(teorias, emb_t, emb_q, sims, res, delta, destino):
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.lines import Line2D
    from sklearn.decomposition import PCA
    pca = PCA(n_components=2, svd_solver="full")
    xy = pca.fit_transform(np.vstack([emb_t, emb_q[None, :]]))
    var = pca.explained_variance_ratio_
    xs, ys = xy[:-1, 0], xy[:-1, 1]
    ids = [t.id for t in teorias]
    fig = plt.figure(figsize=(9, 7.6))
    ax = fig.add_axes([0.085, 0.36, 0.5, 0.52])
    cax = fig.add_axes([0.085, 0.265, 0.5, 0.022])
    tab = fig.add_axes([0.61, 0.265, 0.38, 0.615])
    tab.axis("off")
    cmap = LinearSegmentedColormap.from_list("oscuro", ["#9A3412", "#6B21A8", "#1E3A8A"])
    sc = ax.scatter(xs, ys, c=sims, cmap=cmap, s=140, edgecolors=C_TEXTO,
                    linewidths=1.0, zorder=3)
    cb = fig.colorbar(sc, cax=cax, orientation="horizontal")
    cb.set_label("coseno con la consulta (embeddings, dimensión completa)")
    cb.ax.xaxis.set_major_formatter(
        __import__("matplotlib.ticker", fromlist=["FuncFormatter"]).FuncFormatter(
            lambda v, _: num(v, 2)))
    # puntos apiñados alrededor de la consulta → ampliación (inset) para que se lean
    span = float(max(np.ptp(xy[:, 0]), np.ptp(xy[:, 1])))
    cerca = [i for i in range(len(teorias))
             if np.hypot(xs[i] - xy[-1, 0], ys[i] - xy[-1, 1]) < 0.12 * span]
    axes_dibujo = [ax]
    ins = None
    if len(cerca) >= 3:
        ins = ax.inset_axes([0.47, 0.04, 0.5, 0.46])
        axes_dibujo.append(ins)
        ins.scatter(xs[cerca], ys[cerca], c=[sims[i] for i in cerca], cmap=cmap,
                    vmin=min(sims), vmax=max(sims), s=140, edgecolors=C_TEXTO,
                    linewidths=1.0, zorder=3)
        px = [xs[i] for i in cerca] + [xy[-1, 0]]
        py = [ys[i] for i in cerca] + [xy[-1, 1]]
        mx = (max(px) - min(px)) * 0.35 + 1e-3
        my = (max(py) - min(py)) * 0.35 + 1e-3
        ins.set_xlim(min(px) - mx, max(px) + mx)
        ins.set_ylim(min(py) - my, max(py) + my)
        ins.set_xticks([]); ins.set_yticks([])
        ax.indicate_inset_zoom(ins, edgecolor=C_TEXTO, alpha=0.9)
    for eje in axes_dibujo:
        for i, t in enumerate(teorias):
            if eje is ins and i not in cerca:
                continue
            if t.id in res["recuperadas_top_k"]:
                eje.scatter(xs[i], ys[i], s=420, facecolors="none", edgecolors=C_VERDE,
                            linewidths=2.6, zorder=4)
        sel = res["seleccionada"]
        if sel is not None and (eje is ax or ids.index(sel) in cerca):
            i = ids.index(sel)
            eje.scatter(xs[i], ys[i], s=650, marker="*", color=C_ROJO, edgecolors=C_TEXTO,
                        linewidths=1.0, zorder=5)
        eje.scatter(xy[-1, 0], xy[-1, 1], s=230, marker="X", color=C_AZUL,
                    edgecolors="white", linewidths=1.2, zorder=6)
    sel = res["seleccionada"]
    ax.margins(0.18)
    fuera = [i for i in range(len(teorias)) if ins is None or i not in cerca]
    _etiquetar(ax, fig, [xs[i] for i in fuera], [ys[i] for i in fuera],
               [f"T{ids[i]}" for i in fuera])
    if ins is not None:
        consulta_igual = [i for i in cerca if sims[i] >= 1 - 1e-6]
        _etiquetar(ins, fig, [xs[i] for i in cerca], [ys[i] for i in cerca],
                   [f"T{ids[i]}" + (" = consulta" if i in consulta_igual else "")
                    for i in cerca])
    comas(ax)
    ax.set_xlabel(f"PC1 ({num(var[0] * 100, 1)} % de la varianza)")
    ax.set_ylabel(f"PC2 ({num(var[1] * 100, 1)} % de la varianza)")
    fig.suptitle("D1 · Espacio de embeddings de las Si de la base del Matcher (PCA 2D)",
                 x=0.012, ha="left", y=0.975)
    ley = [Line2D([], [], marker="X", ls="", color=C_AZUL, ms=12, label="consulta: Si de Fátima"),
           Line2D([], [], marker="o", ls="", mfc="none", mec=C_VERDE, mew=2.6, ms=16,
                  label=f"recuperadas (top-{len(res['recuperadas_top_k'])})"),
           Line2D([], [], marker="*", ls="", color=C_ROJO, ms=18, label="seleccionada")]
    ax.legend(handles=ley, loc="upper center", bbox_to_anchor=(0.5, 1.13), ncol=3,
              frameon=False, handletextpad=0.3, columnspacing=0.8, fontsize=12)
    # tabla: T, A, (P, K, U), coseno — ordenada por coseno descendente
    orden = sorted(range(len(teorias)), key=lambda i: -sims[i])
    filas = ["T    A    (P,K,U)     cos"]
    for i in orden:
        t = teorias[i]
        marca = "★" if t.id == sel else ("✓" if t.id in res["recuperadas_top_k"] else " ")
        filas.append(f"T{t.id:<3} {t.a[:3]}  ({t.p},{t.k},{num(t.u, 2)})  "
                     f"{num(sims[i], 3)} {marca}")
    tab.text(0.0, 1.0, "\n".join(filas), family="DejaVu Sans Mono", fontsize=12,
             va="top", ha="left", color=C_TEXTO, linespacing=1.45)
    n_sup = len(res["superan_delta"])
    pie_rotulos(fig, [
        "PCA es una proyección: la selección usa el coseno en la dimensión completa "
        f"({emb_t.shape[1]}). La consulta coincide con la Si de una teoría de la base "
        "(la de Fátima). Recuadro: ampliación alrededor de la consulta.",
        f"Superan δ = {num(delta, 1)}: {n_sup} de {len(teorias)} teorías. Entre las que superan δ "
        "decide la clave de retrieve (U, P, K, recencia, id), no el coseno. "
        "★ seleccionada · ✓ recuperada."], ancho=98)
    return guardar_figura(fig, "d1_espacio_embeddings.png", destino), [round(float(v), 4) for v in var]


def _figura_barras(teorias, tok, emb, delta, destino):
    n = len(teorias)
    fig = plt.figure(figsize=(9, 7.6))
    ax = fig.add_axes([0.33, 0.25, 0.64, 0.63])
    y = np.arange(n)
    h = 0.38 if emb is not None else 0.6
    ax.barh(y - (h / 2 if emb is not None else 0), tok["sims"], height=h, color=C_AZUL,
            label="token-cosine (default)")
    if emb is not None:
        ax.barh(y + h / 2, emb["sims"], height=h, color="#9A3412", label="embeddings")
    ax.axvline(delta, color=C_ROJO, lw=2.2, ls="--", label=f"δ del Matcher = {num(delta, 1)}")
    etiquetas = []
    for t in teorias:
        marcas = []
        for nombre, ev in (("tok", tok), ("emb", emb)):
            if ev is None:
                continue
            if ev["top"] and ev["top"][0] == t.id:
                marcas.append(f"★{nombre}")
            elif t.id in ev["top"]:
                marcas.append(f"✓{nombre}")
        etiquetas.append(f"T{t.id} {t.a[:3]} ({t.p},{t.k},{num(t.u, 2)}) {' '.join(marcas)}")
    ax.set_yticks(y, etiquetas)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.05)
    comas(ax)
    ax.set_yticks(y, etiquetas)
    ax.set_xlabel("similitud con la Si de Fátima (caso 3)")
    fig.suptitle("D1 · Similitud consulta–teoría y recuperación con el δ del Matcher",
                 x=0.012, ha="left", y=0.975)
    ax.legend(loc="upper center", bbox_to_anchor=(0.36, 1.09), ncol=3, frameon=False,
              fontsize=12, handlelength=1.6, columnspacing=1.0)
    pie_rotulos(fig, ["★ seleccionada · ✓ recuperada (top-k) · tok = token-cosine · "
                      "emb = embeddings. Etiqueta: T<id> acción (P, K, U)."
                      + ("" if emb is not None else
                         " Embeddings no disponibles en esta corrida: ver el JSON.")])
    return guardar_figura(fig, "d1_similitud_barras.png", destino)


def correr(out=None, backend: str = "auto") -> dict:
    destino = out_dir(out)
    estilo_figuras()
    pipe = HRPipeline(mode="sim")
    pipe.warmup(CANDIDATES)                         # base "como queda después del lote"
    m = pipe.matcher
    teorias = list(m.theories.theories)
    fatima = get(CASO_CONSULTA)
    q = build_si(normalize_profile(fatima))
    delta = m.retriever.delta
    tok = _evaluar(m, teorias, q, "token-cosine")
    res_tok = _resumen(tok, teorias, delta)

    emb, res_emb, error = None, None, None
    if backend == "auto":
        try:
            emb = _evaluar(m, teorias, q, "embeddings")
            res_emb = _resumen(emb, teorias, delta)
        except Exception as exc:                    # extra no instalado o sin red
            error = f"{type(exc).__name__}: {exc}"

    propia = next((t.id for t in teorias if serialize(t.si) == serialize(q)), None)
    filas = []
    for i, t in enumerate(teorias):
        fila = {"id": t.id, "si": t.si, "a": t.a, "sf": t.sf, "p": t.p, "k": t.k,
                "u": round(t.u, 4), "sim_token_cosine": round(tok["sims"][i], 4),
                "supera_delta_token_cosine": tok["sims"][i] >= delta}
        if emb is not None:
            fila["sim_embeddings"] = round(emb["sims"][i], 4)
            fila["supera_delta_embeddings"] = emb["sims"][i] >= delta
        filas.append(fila)

    salida = {
        "demo": "D1 — selección de teoría por embeddings (P3)",
        "base": {"origen": "warmup de la PoC sobre los 12 candidatos (como run_poc.py)",
                 "n_teorias": len(teorias)},
        "consulta": {"candidato_id": fatima.id, "candidato": fatima.name, "si": q,
                     "teoria_con_la_misma_si": propia},
        "delta": {
            "rige": delta,
            "de_donde_sale": "SemanticMatcherAgent → MOACVAgent(delta=…) → "
                             "TheoryRetriever(delta=…): matcher.retriever.delta",
            "default_TheoryRetriever": inspect.signature(
                TheoryRetriever.__init__).parameters["delta"].default,
            "default_MOACVAgent": inspect.signature(
                MOACVAgent.__init__).parameters["delta"].default,
        },
        "top_k": m.retriever.top_k,
        "clave_de_orden": "(U desc, P desc, K asc, recencia desc, id asc) — "
                          "TheoryRetriever.retrieve; la similitud solo filtra (≥ δ)",
        "teorias": filas,
        "token_cosine": res_tok,
    }
    if emb is not None:
        va = retrieval._EMBEDDER.encode([serialize(t.si) for t in teorias],
                                        normalize_embeddings=True)
        vq = retrieval._EMBEDDER.encode([serialize(q)], normalize_embeddings=True)[0]
        dif = float(np.max(np.abs(va @ vq - np.asarray(emb["sims"]))))
        ruta, var = _figura_pca(teorias, va, vq, emb["sims"], res_emb, delta, destino)
        salida["embeddings"] = {
            "disponible": True,
            "modelo": os.environ.get("MOAV_EMBED_MODEL", MODELO_DEFAULT),
            "dimension": int(va.shape[1]), **res_emb,
            "pca_varianza_explicada": var,
            "verificacion_max_dif_coseno_vs_similarity": round(dif, 8),
            "figura": ruta.name,
        }
        salida["comparacion"] = {
            "misma_seleccionada": res_tok["seleccionada"] == res_emb["seleccionada"],
            "mismas_recuperadas": res_tok["recuperadas_top_k"] == res_emb["recuperadas_top_k"],
            "puesto_de_la_teoria_con_la_misma_si": {
                "token_cosine": (res_tok["ranking_entre_las_que_superan_delta"].index(propia) + 1
                                 if propia in res_tok["ranking_entre_las_que_superan_delta"]
                                 else None),
                "embeddings": (res_emb["ranking_entre_las_que_superan_delta"].index(propia) + 1
                               if propia in res_emb["ranking_entre_las_que_superan_delta"]
                               else None)},
        }
    else:
        salida["embeddings"] = {"disponible": False,
                                "error": error or "no solicitado (--backend token-cosine)"}
        salida["comparacion"] = None
    barras = _figura_barras(teorias, tok, emb, delta, destino)
    salida["figuras"] = [f for f in (salida["embeddings"].get("figura"), barras.name) if f]
    guardar_json(salida, "d1_embeddings.json", destino)
    return salida


def main() -> None:
    ap = argparse.ArgumentParser(description="D1 — selección de teoría por embeddings")
    ap.add_argument("--backend", choices=["auto", "token-cosine"], default="auto",
                    help="auto: embeddings + token-cosine (si el modelo falla, solo "
                         "token-cosine); token-cosine: sin modelo")
    ap.add_argument("--out", default=None, help="carpeta de salida (default docs/demos_direccion)")
    args = ap.parse_args()
    s = correr(args.out, args.backend)
    print(f"D1 · δ que rige = {s['delta']['rige']} · token-cosine selecciona "
          f"T{s['token_cosine']['seleccionada']}", end="")
    if s["embeddings"]["disponible"]:
        print(f" · embeddings selecciona T{s['embeddings']['seleccionada']} · "
              f"misma = {s['comparacion']['misma_seleccionada']}")
    else:
        print(f" · embeddings NO disponible: {s['embeddings']['error']}")


if __name__ == "__main__":
    main()
