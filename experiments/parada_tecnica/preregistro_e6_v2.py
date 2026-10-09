#!/usr/bin/env python
"""
Pre-registro corto de E6 v2 (E6_RESPUESTA de Claude chat, decisión 1): escribe
docs/parada_tecnica/E6_PREREGISTRO_v2.md a partir de la sección `equipo_e6_v2` de la config.
No corre ningún agente.

Uso:  python experiments/parada_tecnica/preregistro_e6_v2.py [--out DIR]
"""
from __future__ import annotations
import argparse

from comun_pt import cargar_config, encabezado_md, out_dir


def escribir(out=None) -> str:
    cfg = cargar_config()
    v2 = cfg["equipo_e6_v2"]
    m_min = cfg["utilidad"]["m_min_por_grupo"]
    L = encabezado_md("E6 v2 · Pre-registro corto: la equidad por celda (Si, A) en la utilidad")
    L += ["Se commitea **antes** de correr, junto con "
          "`docs/parada_tecnica/E6_RESPUESTA_ClaudeChat_2026-10-08.md`. Es la única revisión de "
          "E6; E6 (v1) queda como está. Parámetros: `configs/parada_tecnica.yaml`, sección "
          "`equipo_e6_v2`.", "",
          "## El cambio", "",
          "- **v1:** ê(t) por teoría (variante (Si, A, Sf)), sobre las decisiones en que t fue el "
          "plan. Con U(Si, A) de la v2, todas las variantes de una acción tienen la misma U, así "
          "que ê(t) solo reordenaba variantes de la misma acción (resultado 1 de E6: 175 cambios "
          "de teoría, 0 de acción).",
          "- **v2:** ê(Si, A) = 1 − |tasa de error(AR) − tasa de error(no-AR)| sobre E(Si, A): "
          "todas las decisiones en que se aplicó la acción A en la situación Si, con cualquier "
          "motivo. U_rol(Si, A) = α·U(Si, A) + (1 − α)·ê(Si, A). El orden sigue la Fig. 4.21 "
          "sobre U_rol (después P desc, K asc y el desempate determinista).",
          "- **Candidatas sin ê:** las candidatas son la mejor variante de cada acción de la "
          f"celda. Si alguna no tiene ê (menos de m_min = {m_min} lecturas en algún grupo), la "
          "planificación usa α = 1 para **todas** y se registra «ajuste no aplicable: falta "
          "evidencia». Motivo: el respaldo de la v1 premiaba la falta de evidencia (160 de 175 "
          "cambios).",
          "- **Validez del plan:** sigue usando U (U ≥ 0,5). Si la primera del orden por U_rol no "
          "es un plan válido, se aplica el «azar» de P3, como siempre.", "",
          "## Qué se vuelve a correr", "",
          "- La corrida 1 con α = 0,5, sobre los mismos 600 casos y semillas.",
          "- La condición con sesgo programado con α = 0,5, en las dos magnitudes.",
          "- Las corridas con α = 1 y el neutro no cambian: se toman de E6.", "",
          "## Qué se informa", "",
          "- Cambios de **acción** y de teoría frente a α = 1 (el contrafáctico dentro de la misma "
          "corrida).",
          "- Aciertos y odds igualadas por grupo frente a la corrida con α = 1 (el ajuste puede "
          "costar precisión).",
          "- Cuántas planificaciones no pudieron ajustarse por falta de evidencia.",
          "- La v1 y la v2 lado a lado.", "",
          "**Advertencia (para el documento de la dirección).** Dentro de una celda con la acción "
          "fija, ê(Si, A) mide si esa acción se equivoca más con un grupo que con el otro, lo que "
          "pasa cuando la Si no captura algo relacionado con el grupo. No mide trato desigual: ese "
          "se ve en la ventana.", "",
          "## Control post hoc (decisión 4)", "",
          f"«{v2['control_post_hoc']['rotulo'].capitalize()}». Un Matcher que aprende sobre los "
          "mismos casos de la condición programada, sin el rasgo `titulo_local` y con el operador "
          "BIO sin sesgo (el de P1), con α = 1. Separa la tasa base del sesgo residual. Es "
          "descriptivo: no cambia ninguna regla ni conclusión pre-registrada.", ""]
    ruta = out_dir(out) / "E6_PREREGISTRO_v2.md"
    ruta.write_text("\n".join(L) + "\n", encoding="utf-8")
    return str(ruta)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None)
    print(escribir(ap.parse_args().out))
