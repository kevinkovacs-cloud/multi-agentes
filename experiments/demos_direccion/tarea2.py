"""
Segundo lote (tarea 2) para los demos D2 y D4 — generado de forma DETERMINISTA.

No modifica instances/hr/synthetic.py ni los datos de los tests: arma candidatos nuevos
del MISMO puesto (JOB) a partir de los perfiles de la tarea 1, para que haya Si
repetidas. Regla del generador (semilla fija):

  · cada candidato toma como plantilla un perfil de la tarea 1 (elegido al azar);
  · conserva skills y educación; la experiencia se corre −1, 0 o +1 año (puede cambiar
    la banda de experiencia y, con eso, la Si);
  · match_score y true_qual = los de la plantilla + ruido gaussiano (σ = 0,02),
    redondeados a 2 decimales y acotados a [0,5; 0,99];
  · género, origen y edad se sortean; bias_risk = "high" si el origen es SY, IN o EG
    (los orígenes marcados "high" en la tarea 1), "med" si la edad es > 40, y "low"
    en otro caso. Aproxima el etiquetado de la tarea 1; no lo replica.
"""
from __future__ import annotations
import random

from moav_hr.instances.hr.synthetic import CANDIDATES, Candidate

SEMILLA = 20260929
N_TAREA2 = 12
_ORIGENES = ("AR", "AR", "AR", "BR", "CL", "CO", "SY", "IN", "EG")


def _acotar(x: float) -> float:
    return round(min(0.99, max(0.5, x)), 2)


def generar_tarea2_con_plantillas(n: int = N_TAREA2,
                                  semilla: int = SEMILLA) -> list[tuple[Candidate, int]]:
    """Candidatos de la tarea 2 junto con el id de su plantilla de la tarea 1."""
    rng = random.Random(semilla)
    out = []
    for i in range(n):
        plantilla = rng.choice(CANDIDATES)
        exp = max(0, plantilla.exp + rng.choice((-1, 0, 1)))
        genero = rng.choice(("F", "M"))
        origen = rng.choice(_ORIGENES)
        edad = rng.randint(23, 50)
        riesgo = "high" if origen in ("SY", "IN", "EG") else "med" if edad > 40 else "low"
        out.append((Candidate(
            id=101 + i, name=f"Postulante T2-{i + 1:02d}", gender=genero, age=edad,
            origin=origen, exp=exp, edu=plantilla.edu, skills=plantilla.skills,
            match_score=_acotar(plantilla.match_score + rng.gauss(0.0, 0.02)),
            bias_risk=riesgo,
            true_qual=_acotar(plantilla.true_qual + rng.gauss(0.0, 0.02))), plantilla.id))
    return out


def generar_tarea2(n: int = N_TAREA2, semilla: int = SEMILLA) -> list[Candidate]:
    return [c for c, _ in generar_tarea2_con_plantillas(n, semilla)]
