#!/usr/bin/env python
"""
Pre-registro v2 del Bloque E: escribe docs/parada_tecnica/E2_PREREGISTRO_v2.md y la
característica del gate de Ω v2 (p1_gate_caracteristica.png). Solo usa `core/stats`: no corre
ningún agente.

Característica: para n decisiones por grupo y L cierres posibles en la capa, la brecha mínima
de paridad |p̂_a − p̂_b| que hace negar la promoción (LCB_{δ/L}(|Δ|) > τ_b, Hoeffding por grupo,
`stats.lcb_abs_diff_rates`).

Uso:  python experiments/parada_tecnica/preregistro_v2.py [--out DIR]
"""
from __future__ import annotations
import argparse

from comun_pt import (C_AZUL, C_ROJO, C_TEXTO, C_VERDE, cargar_config, encabezado_md,
                      estilo_figuras, num, out_dir, pie_rotulos, plt)
from moav_hr.core import stats

NS = (10, 20, 30, 40, 50, 75, 100, 150, 200)


def brecha_minima(n: int, L: int, delta: float, tau_b: float):
    """Menor brecha k/n (n por grupo) con LCB_{δ/L} > τ_b; None si ninguna alcanza."""
    for k in range(n + 1):
        if stats.lcb_abs_diff_rates(k, n, 0, n, delta / L) > tau_b:
            return k / n
    return None


def escribir(out=None) -> str:
    destino = out_dir(out)
    estilo_figuras()
    cfg = cargar_config()
    om, cv = cfg["omega"], cfg["ciclo_de_vida"]
    Ls = sorted({cv["ciclos_por_capa"][c] // cv["n_intervalo"] for c in ("BIO", "TBO", "WIO")})
    tabla = {L: [brecha_minima(n, L, om["delta"], om["tau_b"]) for n in NS] for L in Ls}
    fig = plt.figure(figsize=(9, 6.6))
    ax = fig.add_axes([0.1, 0.3, 0.86, 0.6])
    for L, col in zip(Ls, (C_AZUL, C_VERDE, C_ROJO)):
        xs = [n for n, b in zip(NS, tabla[L]) if b is not None]
        ys = [b for b in tabla[L] if b is not None]
        ax.plot(xs, ys, "-o", color=col, lw=2.4, ms=7, label=f"L = {L} cierres")
    ax.axhline(om["tau_b"], color=C_TEXTO, ls="--", lw=1.6, label=f"τ_b = {num(om['tau_b'], 3)}")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("decisiones por grupo acumuladas en la capa (n)")
    ax.set_ylabel("brecha mínima que hace negar")
    ax.legend(loc="upper right", framealpha=0.95)
    from matplotlib.ticker import FuncFormatter
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
    fig.suptitle("Gate de Ω v2: brecha de paridad mínima que niega la promoción",
                 x=0.012, ha="left", y=0.975, fontsize=14)
    pie_rotulos(fig, [
        f"Ω niega solo si LCB_δ/L(|Δ_DP|) > τ_b (Hoeffding por grupo, δ = {num(om['delta'], 2)}). "
        "Sin punto: con ese n no hay brecha que alcance. Se calcula con core/stats, sin correr "
        "agentes."], ancho=98)
    fig.savefig(destino / "p1_gate_caracteristica.png", dpi=200, facecolor="white")
    plt.close(fig)

    L_ = encabezado_md("E2 · Pre-registro v2 (antes de correr P1 v2, P2b v2 y E3)")
    L_ += ["Única revisión, decidida por Claude chat con delegación de Kevin "
           "(`docs/parada_tecnica/E2_RESPUESTA_ClaudeChat_2026-10-08.md`). La v1 sigue en "
           "`configs/parada_tecnica_v1.yaml` y su corrida queda en el informe como resultado "
           "pre-registrado.", "",
           "## Cambios y motivos", "",
           "1. **Gate de Ω para la evolución.** Ω niega la promoción solo si hay evidencia de "
           f"sesgo: LCB_δ/L(|Δ_DP|) > τ_b = {num(om['tau_b'], 3)} sobre todas las decisiones del "
           f"agente en la capa, con δ = {num(om['delta'], 2)} y L = cierres posibles de la capa "
           "(Bonferroni). La reputación r y el certificado se informan pero no deciden. Motivo: "
           "con ventanas de 20 el gate puntual era ruido de muestreo; es el mismo primitivo que "
           "la regla de bloqueo publicada.",
           "2. **U basada en la acción.** U(Si, A) = (aciertos de A en la celda + 1)/(K(Si, A) + "
           "2), igual para todas las variantes (Si, A, ·); los aciertos son la suma de los P de "
           "las variantes cuya Sf hace correcta la acción. P y K siguen la Fig. 4.13 y ΣP = K se "
           "mantiene. Orden de la Fig. 4.21 literal sobre (U, P, K). Validez del plan: U ≥ 0,5. "
           "Rango [0, 1] (en la tesis, [−1, 1]). Motivo: §4.4.3.2 (pp. 89–90), p. 107 y la "
           "recomendación 2(a) de la hoja.",
           "3. **Evaluación acumulada en la capa.** CE_a, CE_0 y las teorías nuevas se acumulan "
           "desde el inicio de la capa hasta cada cierre; %TN = teorías nuevas / ciclos en la "
           "capa. Motivo: p. 118 y Fig. 4.28.",
           "4. **Compartición (E3).** Se rechaza al donante si hay evidencia de sesgo en sus "
           "decisiones (LCB_δ > τ_b) o si no cumple `can_donate` "
           f"(≥ {cfg['compartir']['m0_historia_minima']} ventanas). Equipos: "
           + ", ".join(f"{k} = {v}" for k, v in cfg["compartir"]["equipos"].items())
           + ". Solo estados ganados: si falta uno, se frena y se avisa.", "",
           "**Sin cambios:** semilla, n, ciclos por capa, %RCE, %RTN, umbral de ciclo exitoso, ε "
           "de WIO, τ_b y δ. Ciclo exitoso: la acción del ciclo fue correcta, igual para el "
           "agente y para el SAR neutro.", "",
           "## Característica del gate v2 (`p1_gate_caracteristica.png`)", "",
           "Brecha de paridad mínima (|p̂_a − p̂_b|, con n decisiones por grupo acumuladas en la "
           "capa) que hace negar la promoción. «—» = con ese n ninguna brecha alcanza.", "",
           "| n por grupo | " + " | ".join(f"L = {L}" for L in Ls) + " |",
           "|---|" + "---|" * len(Ls)]
    for i, n in enumerate(NS):
        L_.append(f"| {n} | " + " | ".join("—" if tabla[L][i] is None else num(tabla[L][i], 3)
                                           for L in Ls) + " |")
    L_ += ["", "Con decenas de decisiones por capa, Ω solo puede frenar ante evidencia de un "
           "sesgo grande; certificar equidad en positivo exige historias largas (m_min = 47 "
           "ventanas).", ""]
    texto = "\n".join(L_)
    (destino / "E2_PREREGISTRO_v2.md").write_text(texto, encoding="utf-8")
    return texto


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Pre-registro v2 (Bloque E)")
    ap.add_argument("--out", default=None)
    escribir(ap.parse_args().out)
    print("E2_PREREGISTRO_v2.md y p1_gate_caracteristica.png escritos")
