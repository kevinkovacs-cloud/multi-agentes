#!/usr/bin/env python
"""
Métricas descriptivas de E5 (E5_RESPUESTA_ClaudeChat_2026-10-08.md, decisiones 1 y 2). Se
calculan sobre las MISMAS corridas de E5: el script las reconstruye en memoria (son
deterministas) y verifica que el contenido de p3_equipos.json sale idéntico, byte a byte, al
commiteado; si no, se detiene. No cambia ninguna regla ni ninguna promoción.

  1. Desempeño de cada rol y del equipo frente al equipo neutro N: aciertos del rol con las
     entradas de su propio equipo, frente a los del rol neutro con las entradas del equipo
     neutro (B, B0 y BC procesan los mismos casos que N).
  2. Curvas de aprendizaje sin piso (estadísticas del LLC, §4.4.9): ciclos exitosos y teorías
     nuevas acumulados por rol y por ciclo; y el primer ciclo en que se cumpliría la regla de
     evolución si se evaluara en cada ciclo y no solo al cierre del intervalo.

Salidas: docs/parada_tecnica/p3_descriptivas.json y p3_curvas_aprendizaje.png.

Uso:  python experiments/parada_tecnica/p3_descriptivas.py [--out DIR]
"""
from __future__ import annotations
import argparse

from comun_pt import (OUT_DEFAULT, C_AMBAR, C_AZUL, C_ROJO, C_TEXTO, cargar_config,
                      estilo_figuras, guardar_json, out_dir, pie_rotulos, plt, texto_json)
from p3_equipos_dag import FIGURA, TITULO, ejecutar, resultados
from moav_hr.core.ciclo_llc import evaluar_regla

ROLES = ("parser", "matcher", "explainer")
MISMOS_CASOS = ("B", "B0", "BC")


def frente_al_neutro(eqs: dict) -> dict:
    """Decisión 1: aciertos de cada rol y del equipo frente al equipo neutro N."""
    def por_caso(eq):
        return [{"parser": ce.ciclos["parser"]["exitoso"],
                 "matcher": ce.ciclos["matcher"]["exitoso"],
                 "explainer": ce.ciclos["explainer"]["exitoso"]} for ce in eq.casos]
    n = por_caso(eqs["N"])
    base = {r: sum(int(x[r]) for x in n) for r in ROLES}
    base["equipo"] = sum(int(all(x.values())) for x in n)
    out = {"N": base, "casos": len(n)}
    for e in MISMOS_CASOS:
        x = por_caso(eqs[e])
        fila = {r: sum(int(c[r]) for c in x) for r in ROLES}
        fila["equipo"] = sum(int(all(c.values())) for c in x)
        out[e] = {k: {"aciertos": v, "neutro": base[k],
                      "mejora_pct": round(100.0 * (v - base[k]) / max(base[k], 1), 1)}
                  for k, v in fila.items()}
    return out


def curvas(eq) -> dict:
    out = {}
    for r in ROLES:
        ex, tn, a, b = [], [], 0, 0
        for reg in eq.motores[r].ciclos:
            a += int(reg["exitoso"])
            b += reg["registro"] in ("nueva", "similar")
            ex.append(a)
            tn.append(b)
        out[r] = {"exitosos_acumulados": ex, "teorias_nuevas_acumuladas": tn}
    return out


def regla_en_cada_ciclo(eq, cfg: dict) -> dict:
    """Decisión 2: primer ciclo de cada capa en que la regla de evolución se cumpliría si se
    evaluara en cada ciclo (acumulada en la capa, como la v2), y desde qué ciclo se cumple sin
    interrupción hasta el cierre real. Descriptivo: la promoción real es al cierre."""
    cv = cfg["ciclo_de_vida"]
    out = {}
    for r in ROLES:
        m = eq.motores[r]
        if not getattr(eq.roles[r], "evoluciona", True):
            continue
        cierre = {e["capa"]: e["ciclo_capa"] for e in m.evaluaciones if e["promueve"]}
        filas = []
        for capa in ("BIO", "TBO", "WIO"):
            regs = [x for x in m.ciclos if x["capa"] == capa and x.get("sin_r7") is None]
            if not regs:
                continue
            fin = cierre.get(capa, cv["ciclos_por_capa"][capa])
            regs = [x for x in regs if x["ciclo_capa"] <= fin]
            n_cierres = cv["ciclos_por_capa"][capa] // cv["n_intervalo"]
            ce_a = ce_0 = nuevas = 0
            decs, cumple = [], []
            for x in regs:
                ce_a += int(x["exitoso"])
                ce_0 += int(x["acierto_bio"])
                nuevas += x["registro"] in ("nueva", "similar")
                decs += [{m.cfg.attr: g, "decision": "ADVANCE" if f else "REJECT"}
                         for g, f in (x.get("equidad") or [])]
                gate = m.monitor.gate_evidencia_sesgo(decs, n_cierres, m.cfg.delta_omega)
                ev = evaluar_regla(ce_a, ce_0, nuevas, x["ciclo_capa"],
                                   m.recibio_colaboracion[capa], gate["aprueba"],
                                   m.cfg.rce, m.cfg.rtn)
                cumple.append((x["ciclo_capa"], ev["promueve"]))
            primero = next((j for j, ok in cumple if ok), None)
            sostenido = None
            for j, ok in reversed(cumple):
                if not ok:
                    break
                sostenido = j
            filas.append({"capa": capa, "ciclos_evaluados": len(cumple),
                          "promocion_real": cierre.get(capa), "primer_ciclo_que_cumple": primero,
                          "cumple_sin_interrupcion_desde": sostenido})
        out[r] = filas
    return out


def figura(cur: dict, destino) -> str:
    estilo_figuras()
    series = [("B", "B · colaboración de A", C_AZUL, "-"), ("B0", "B0 · sin compartir", C_ROJO, "-"),
              ("C", "C · otra semilla", C_AMBAR, "--"), ("N", "N · neutro", C_TEXTO, ":")]
    fig, axs = plt.subplots(len(ROLES), 2, figsize=(9, 10.4), sharex=True)
    fig.subplots_adjust(left=0.1, right=0.98, top=0.9, bottom=0.17, hspace=0.38, wspace=0.28)
    for i, r in enumerate(ROLES):
        for j, (clave, nombre) in enumerate((("exitosos_acumulados", "ciclos exitosos"),
                                             ("teorias_nuevas_acumuladas", "teorías nuevas"))):
            ax = axs[i][j]
            for e, etiqueta, col, ls in series:
                ys = cur[e][r][clave]
                ax.plot(range(1, len(ys) + 1), ys, color=col, lw=2.2, ls=ls, label=etiqueta)
            ax.set_title(f"{TITULO[r]}: {nombre}", loc="left", fontsize=14)
            ax.grid(color=C_TEXTO, alpha=0.15)
    for ax in axs[-1]:
        ax.set_xlabel("ciclo del rol")
    axs[0][0].legend(loc="lower right", framealpha=0.95, fontsize=12)
    fig.suptitle("Curvas de aprendizaje sin piso (acumuladas por ciclo)", x=0.012, ha="left",
                 y=0.975, fontsize=14)
    pie_rotulos(fig, ["B, B0 y N procesan los mismos casos; C, los de su semilla. Estadísticas "
                      "del LLC (§4.4.9); descriptivo: no cambia ninguna promoción."], ancho=98)
    ruta = destino / "p3_curvas_aprendizaje.png"
    fig.savefig(ruta, dpi=200, facecolor="white")
    plt.close(fig)
    return ruta.name


def correr(out=None, commiteado=None) -> dict:
    cfg = cargar_config()
    destino = out_dir(out)
    corrida = ejecutar(cfg)
    res = resultados(cfg, corrida)
    res["figura"] = FIGURA
    ref = commiteado or (OUT_DEFAULT / "p3_equipos.json")
    if texto_json(res) != ref.read_text(encoding="utf-8"):
        raise SystemExit("la corrida reconstruida no coincide con p3_equipos.json: se detiene")
    eqs = corrida["eqs"]
    cur = {e: curvas(eqs[e]) for e in ("A", "B", "B0", "BC", "C", "N")}
    out = {"misma_corrida": "p3_equipos.json reconstruido idéntico byte a byte",
           "frente_al_neutro": frente_al_neutro(eqs),
           "regla_en_cada_ciclo": {e: regla_en_cada_ciclo(eqs[e], cfg)
                                   for e in ("A", "B", "B0", "BC", "C")},
           "curvas": cur, "figura": figura(cur, destino)}
    guardar_json(out, "p3_descriptivas.json", destino)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None)
    r = correr(ap.parse_args().out)
    import json
    print(json.dumps({"frente_al_neutro": r["frente_al_neutro"],
                      "regla_en_cada_ciclo": r["regla_en_cada_ciclo"]}, ensure_ascii=False,
                     indent=1)[:4000])
