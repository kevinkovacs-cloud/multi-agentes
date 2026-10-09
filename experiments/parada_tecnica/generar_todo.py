#!/usr/bin/env python
"""
Bloque E · E7: corre todo lo de la «parada técnica» y regenera las salidas y los informes.

Orden: corridas (P1, P2b, P2a, P4, P3, P5, E6 v2 y el control post hoc), documentos de
pre-registro (se generan desde la config), informes de cada punto de control, el documento de
métricas por rol, el informe final y el guion de la reunión.

  python experiments/parada_tecnica/generar_todo.py                # escribe en docs/parada_tecnica
  python experiments/parada_tecnica/generar_todo.py --verificar    # escribe en un directorio
      temporal y compara byte a byte con lo commiteado en docs/parada_tecnica

Algunos documentos están escritos a mano y no se regeneran: el diagnóstico E0, las respuestas
de Claude chat y el pre-registro corto de E3 (sin números).
"""
from __future__ import annotations
import argparse
import tempfile
import time
from pathlib import Path

import e4_muestreo
import informe_e2
import informe_e3
import informe_e4
import informe_e5
import informe_e6
import informe_final
import metricas_equidad_doc
import p1_teoria_punto_a_punto as p1
import p2a_compartir
import p2a_cooperacion_a9
import p2b_planificador
import p3_descriptivas
import p3_equipos_dag
import p4_traza
import p5_control_post_hoc
import p5_equidad_v2
import p5_metricas_equidad
import preregistro
import preregistro_e4
import preregistro_e5
import preregistro_e6
import preregistro_e6_v2
import preregistro_v2
from comun_pt import OUT_DEFAULT

A_MANO = ("E0_DIAGNOSTICO.md", "E3_PREREGISTRO_A9.md")


def pasos() -> list[tuple[str, object]]:
    return [
        ("P1 v1 (punto 1)", lambda o: p1.correr(o, "v1")),
        ("P1 v2 (punto 1)", lambda o: p1.correr(o, "v2")),
        ("P2b v1 (punto 2b)", lambda o: p2b_planificador.correr(o, "v1")),
        ("P2b v2 (punto 2b)", lambda o: p2b_planificador.correr(o, "v2")),
        ("P2a (punto 2a)", p2a_compartir.correr),
        ("P2a, cooperación con A9 en decisiones", p2a_cooperacion_a9.correr),
        ("P4 (punto 4)", p4_traza.correr),
        ("P3 (punto 3)", p3_equipos_dag.correr),
        ("Muestreo del resultado 5 de E4", e4_muestreo.correr),
        ("P3, métricas descriptivas",
         lambda o: p3_descriptivas.correr(o, commiteado=Path(o) / "p3_equipos.json")),
        ("P5 (punto 5)", p5_metricas_equidad.correr),
        ("E6 v2", p5_equidad_v2.correr),
        ("Control post hoc", p5_control_post_hoc.correr),
        ("Pre-registro del entorno (E2)", preregistro.escribir),
        ("Pre-registro v2 (E2)", preregistro_v2.escribir),
        ("Pre-registro E4", preregistro_e4.escribir),
        ("Pre-registro E5", preregistro_e5.escribir),
        ("Pre-registro E6", preregistro_e6.escribir),
        ("Pre-registro E6 v2", preregistro_e6_v2.escribir),
        ("Informe E2 v1", lambda o: informe_e2.escribir(o, "v1")),
        ("Informe E2 v2", lambda o: informe_e2.escribir(o, "v2")),
        ("E2, v1 y v2 lado a lado", informe_e2.comparar),
        ("Informe E3", informe_e3.escribir),
        ("Informe E4", informe_e4.escribir),
        ("Informe E5", informe_e5.escribir),
        ("Métricas de equidad por rol", metricas_equidad_doc.escribir),
        ("Informe E6", informe_e6.escribir),
        ("Informe final y guion de la reunión", informe_final.escribir),
    ]


def generar(out: Path) -> list[tuple[str, float]]:
    tiempos = []
    for nombre, f in pasos():
        t = time.time()
        f(out)
        tiempos.append((nombre, round(time.time() - t, 1)))
        print(f"  {nombre}: {tiempos[-1][1]} s", flush=True)
    return tiempos


def cambios_sin_commitear(carpeta: Path) -> list[str]:
    """Archivos de `carpeta` con cambios o sin seguimiento en git: la comparación es contra lo
    commiteado solo si esta lista está vacía."""
    import subprocess
    r = subprocess.run(["git", "status", "--porcelain", "--", str(carpeta)], cwd=carpeta,
                       capture_output=True, text=True)
    return [x for x in r.stdout.splitlines() if x.strip()]


def comparar(nuevo: Path, commiteado: Path) -> dict:
    gen = {p.relative_to(nuevo) for p in nuevo.rglob("*") if p.is_file()}
    com = {p.relative_to(commiteado) for p in commiteado.rglob("*") if p.is_file()}
    distintos = sorted(str(p) for p in gen & com
                       if (nuevo / p).read_bytes() != (commiteado / p).read_bytes())
    return {"generados": len(gen), "iguales": len(gen & com) - len(distintos),
            "distintos": distintos, "solo_generados": sorted(str(p) for p in gen - com),
            "no_regenerados": sorted(str(p) for p in com - gen)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verificar", action="store_true",
                    help="genera en un directorio temporal y compara con docs/parada_tecnica")
    a = ap.parse_args()
    if not a.verificar:
        generar(OUT_DEFAULT)
    else:
        with tempfile.TemporaryDirectory() as tmp:
            generar(Path(tmp))
            r = comparar(Path(tmp), OUT_DEFAULT)
        print(f"generados {r['generados']}; iguales byte a byte {r['iguales']}")
        print("distintos:", r["distintos"] or "ninguno")
        print("generados que no están commiteados:", r["solo_generados"] or "ninguno")
        print("commiteados que no se regeneran:", r["no_regenerados"])
        pendientes = cambios_sin_commitear(OUT_DEFAULT)
        print("cambios sin commitear en docs/parada_tecnica:", pendientes or "ninguno")
        esperados = {n for n in r["no_regenerados"]
                     if n in A_MANO or "_RESPUESTA_" in n}
        if r["distintos"] or set(r["no_regenerados"]) - esperados or pendientes:
            raise SystemExit(1)
