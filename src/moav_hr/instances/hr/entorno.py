"""
Entorno simulado por capa para el modo LLC — instancia HR (bloque E · DE-8, P1 y P3).

REGLAS PRE-REGISTRADAS. Se fijaron y documentaron ANTES de la primera corrida de P1, en un
commit propio junto con `configs/parada_tecnica.yaml`; no se ajustan después para que algo
«dé». Un cambio va en un commit nuevo, con su motivo, y se reporta en el informe.

Análogo del simulador del LLC (Webots, §4.6): un escenario por capa (BIO, TBO, WIO) con
complejidad creciente, como en §4.5 (Ierache 2010, pp. 124–126). Casos sintéticos
generados con semilla. El entorno responde DESPUÉS de la acción (región 3), nunca antes.

1. Catálogo de situaciones (Si = build_si: skills clave, banda de experiencia, educación y
   antigüedad mínima). Acotado, para que las teorías se reutilicen:
     · BIO: educación {Licenciatura} × banda {junior, senior} × skills clave {0..3} = 8 celdas;
     · TBO: educación {Licenciatura, Maestría} × lo mismo = 16 celdas (8 nuevas);
     · WIO: educación {Licenciatura, Maestría, Doctorado} × lo mismo = 24 celdas (8 nuevas).
   Frecuencia: uniforme sobre las celdas del catálogo de la capa. La banda «mid» no aparece.
2. Verdad latente (calificado sí/no), igual para todos los grupos: con probabilidad 0,9 si la
   Si cumple los requisitos del puesto (antigüedad mínima y al menos 1 skill clave) y con
   probabilidad 0,1 si no. La educación no cambia la verdad.
3. Operador BIO del Matcher (regla del diseñador, imperfecta a propósito): ADVANCE si la Si
   tiene al menos 2 skills clave; REJECT si no. Ignora la antigüedad y es exigente con los
   skills, así que la mayoría de las veces se equivoca en 3 de cada 8 celdas: junior con 2 o 3
   skills (avanza a no calificados) y senior con 1 skill (rechaza a calificados). Si
   acertara todo, nadie podría superar al SAR neutro (P1).
4. Respuesta del entorno en la región 3 (Sf = {"calificado": …}):
     · BIO y TBO: la etiqueta del escenario de entrenamiento (la verdad latente del caso);
     · WIO: la revisión humana simulada (`human_sim`, modo `noisy`), que invierte la verdad
       con probabilidad ε (configs: `ruido_wio_epsilon`).
5. Atributo protegido: el grupo (AR / no-AR) se asigna alternado por índice de caso (en cada
   intervalo de 20 hay 10 y 10), independiente de la Si y de la verdad. Vive solo en el
   plano de auditoría (Ω y E(t)); nunca entra en Si, en A ni en los prompts (DE-4).
6. Campos del Candidate que el modo LLC no usa: match_score = 0,0 y bias_risk = "low".
   true_qual codifica la verdad latente para human_sim (0,85 calificado / 0,65 no).

`describir_entorno()` calcula, a partir de estas reglas y SIN correr ningún agente, la tabla
de celdas, su frecuencia, la precisión esperada del operador BIO por celda y la de la mejor
acción por celda; `experiments/parada_tecnica/preregistro.py` la escribe en
`docs/parada_tecnica/E2_PREREGISTRO_ENTORNO.md`.
"""
from __future__ import annotations
import itertools
import random
from dataclasses import dataclass

from moav_hr.instances.hr.human_sim import resolve as human_resolve
from moav_hr.instances.hr.parser_agent import build_si, normalize_profile
from moav_hr.instances.hr.synthetic import JOB, Candidate

ACCIONES = ("ADVANCE", "REJECT")
CAPAS = ("BIO", "TBO", "WIO")
SKILLS_CLAVE = tuple(JOB["key_skills"])
SKILLS_OTRAS = ("Java", "SQL", "Docker", "React", "AWS", "Scrum")   # conocidas por el Parser
CATALOGO = {
    "BIO": {"edu": ("Licenciatura",), "banda": ("junior", "senior"), "skills": (0, 1, 2, 3)},
    "TBO": {"edu": ("Licenciatura", "Maestría"), "banda": ("junior", "senior"),
            "skills": (0, 1, 2, 3)},
    "WIO": {"edu": ("Licenciatura", "Maestría", "Doctorado"), "banda": ("junior", "senior"),
            "skills": (0, 1, 2, 3)},
}
Q_REQUISITOS, Q_SIN_REQUISITOS = 0.9, 0.1
TQ_CALIFICADO, TQ_NO_CALIFICADO = 0.85, 0.65
ORIGENES_NO_AR = ("BR", "CL", "CO", "SY", "IN", "EG")


def cumple_requisitos(si: dict) -> bool:
    """Requisitos del puesto (JOB): antigüedad mínima y al menos 1 skill clave."""
    return bool(si["seniority_ok"]) and si["skills_match"] >= 1


def prob_calificado(si: dict) -> float:
    return Q_REQUISITOS if cumple_requisitos(si) else Q_SIN_REQUISITOS


def operador_bio_matcher(si: dict) -> str:
    """Operador BIO del Matcher (regla del diseñador): ADVANCE si hay ≥ 2 skills clave."""
    return "ADVANCE" if si["skills_match"] >= 2 else "REJECT"


@dataclass(frozen=True)
class Caso:
    """Caso del escenario: el candidato (lo que se percibe) y su verdad latente (que el
    agente nunca lee: el entorno la usa recién en la región 3)."""
    indice: int
    capa: str
    candidato: Candidate
    calificado: bool

    @property
    def grupo(self) -> str:
        return self.candidato.origin_group


def _anios(banda: str, rng: random.Random) -> int:
    return rng.randint(0, 2) if banda == "junior" else rng.randint(8, 15)


def generar_escenario(capa: str, n: int, semilla: int) -> list[Caso]:
    """n casos de la capa, con semilla propia de la capa (semilla + índice de la capa)."""
    if capa not in CAPAS:
        raise ValueError(f"capa debe ser una de {CAPAS}")
    rng = random.Random(semilla + CAPAS.index(capa))
    cat = CATALOGO[capa]
    celdas = list(itertools.product(cat["edu"], cat["banda"], cat["skills"]))
    casos = []
    for i in range(n):
        edu, banda, s = rng.choice(celdas)
        skills = tuple(rng.sample(SKILLS_CLAVE, s) + rng.sample(SKILLS_OTRAS, 3 - s))
        exp = _anios(banda, rng)
        no_ar = i % 2 == 1
        origen = ORIGENES_NO_AR[(i // 2) % len(ORIGENES_NO_AR)] if no_ar else "AR"
        genero = "F" if (i // 2) % 2 == 0 else "M"
        edad = rng.randint(23, 50)
        cand_tmp = Candidate(0, "", genero, edad, origen, exp, edu, skills, 0.0, "low", 0.0)
        si = build_si(normalize_profile(cand_tmp))
        calificado = rng.random() < prob_calificado(si)
        cand = Candidate(id=10_000 * (CAPAS.index(capa) + 1) + i,
                         name=f"Caso {capa}-{i + 1:03d}", gender=genero, age=edad,
                         origin=origen, exp=exp, edu=edu, skills=skills, match_score=0.0,
                         bias_risk="low",
                         true_qual=TQ_CALIFICADO if calificado else TQ_NO_CALIFICADO)
        casos.append(Caso(i, capa, cand, calificado))
    return casos


def caso_con_si(si: dict, indice: int, grupo: str = "AR", semilla: int = 0) -> Caso:
    """Caso con una Si dada (para P2b). La verdad sale de la misma regla del entorno."""
    rng = random.Random(semilla + indice)
    s = si["skills_match"]
    skills = tuple(rng.sample(SKILLS_CLAVE, s) + rng.sample(SKILLS_OTRAS, 3 - s))
    exp = {"junior": 1, "mid": 5, "senior": 10}[si["exp_band"]]
    origen = "AR" if grupo == "AR" else "SY"
    calificado = rng.random() < prob_calificado(si)
    cand = Candidate(90_000 + indice, f"Caso P2b-{indice}", "F", 30, origen, exp, si["edu"],
                     skills, 0.0, "low", TQ_CALIFICADO if calificado else TQ_NO_CALIFICADO)
    return Caso(indice, "P2b", cand, calificado)


def observar(caso: Caso, capa: str, epsilon: float, semilla: int) -> dict:
    """Región 3: la situación final la da el entorno DESPUÉS de la acción."""
    if capa in ("BIO", "TBO"):
        return {"calificado": caso.calificado}
    registro = {"true_qual": caso.candidato.true_qual, "origin_group": caso.grupo}
    decision = human_resolve([registro], mode="noisy", seed=semilla + caso.indice,
                             epsilon=epsilon)[0]
    return {"calificado": decision == "ADVANCE"}


def describir_entorno(epsilon: float) -> dict:
    """Tabla del pre-registro, calculada de las reglas (sin correr ningún agente)."""
    out = {}
    for capa in CAPAS:
        cat = CATALOGO[capa]
        celdas = list(itertools.product(cat["edu"], cat["banda"], cat["skills"]))
        filas = []
        for edu, banda, s in celdas:
            si = {"skills_match": s, "exp_band": banda, "edu": edu,
                  "seniority_ok": banda != "junior"}
            q = prob_calificado(si)
            bio = operador_bio_matcher(si)
            p_bio = q if bio == "ADVANCE" else 1 - q
            mejor = "ADVANCE" if q >= 0.5 else "REJECT"
            p_mejor = max(q, 1 - q)
            if capa == "WIO":                 # se mide contra la revisión humana con ruido ε
                p_bio = p_bio * (1 - epsilon) + (1 - p_bio) * epsilon
                p_mejor = p_mejor * (1 - epsilon) + (1 - p_mejor) * epsilon
            filas.append({"si": si, "frecuencia": 1 / len(celdas), "prob_calificado": q,
                          "accion_bio": bio, "precision_bio": round(p_bio, 4),
                          "mejor_accion": mejor, "precision_mejor": round(p_mejor, 4)})
        out[capa] = {"celdas": filas, "n_celdas": len(celdas),
                     "precision_esperada_bio": round(sum(f["precision_bio"] for f in filas)
                                                     / len(filas), 4),
                     "precision_esperada_mejor": round(sum(f["precision_mejor"] for f in filas)
                                                       / len(filas), 4)}
    return out
