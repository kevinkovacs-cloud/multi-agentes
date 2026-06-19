"""
Candidatos sintéticos con atributos demográficos controlados (instancia HR, §4).

ms = match_score (con sesgo implícito simulado) · tq = true_qual (ground-truth) · br = bias_risk
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    id: int
    name: str
    gender: str          # "F" | "M"
    age: int
    origin: str          # ISO-2
    exp: int
    edu: str
    skills: tuple[str, ...]
    match_score: float    # ms
    bias_risk: str        # "low" | "med" | "high"
    true_qual: float      # tq

    @property
    def is_intersectional(self) -> bool:
        return self.gender == "F" and self.origin != "AR"

    @property
    def origin_group(self) -> str:
        return "AR" if self.origin == "AR" else "no-AR"


JOB = {
    "id": "JOB-IT-2026-003",
    "title": "Ingeniero/a de IA",
    "key_skills": ("Python", "ML", "NLP", "TF", "PyTorch", "Spark", "CUDA"),
    "min_exp": 3,
}

CANDIDATES: list[Candidate] = [
    Candidate(1,  "Ana García",       "F", 28, "AR", 5,  "Licenciatura",    ("Python", "ML", "SQL"),       0.87, "low",  0.88),
    Candidate(2,  "Carlos Méndez",    "M", 34, "AR", 8,  "Maestría",        ("Java", "DevOps", "AWS"),     0.91, "low",  0.90),
    Candidate(3,  "Fátima Al-Hassan", "F", 26, "SY", 3,  "Licenciatura",    ("Python", "NLP", "PyTorch"),  0.79, "high", 0.85),
    Candidate(4,  "Miguel Torres",    "M", 41, "AR", 15, "Doctorado",       ("R", "Stats", "Spark"),       0.83, "med",  0.84),
    Candidate(5,  "Valentina Cruz",   "F", 31, "CL", 7,  "Maestría",        ("React", "Node", "GCP"),      0.88, "low",  0.87),
    Candidate(6,  "Diego Ríos",       "M", 29, "AR", 4,  "Licenciatura",    ("Python", "TF", "Docker"),    0.76, "low",  0.75),
    Candidate(7,  "Priya Sharma",     "F", 27, "IN", 4,  "Maestría",        ("Python", "CV", "CUDA"),      0.82, "high", 0.88),
    Candidate(8,  "Roberto Silva",    "M", 38, "BR", 12, "Maestría",        ("Spark", "Kafka", "Scala"),   0.85, "low",  0.86),
    Candidate(9,  "Laura Benítez",    "F", 33, "AR", 9,  "Especialización", ("Scrum", "PM", "Jira"),       0.80, "med",  0.79),
    Candidate(10, "Ahmed El-Sayed",   "M", 30, "EG", 5,  "Licenciatura",    ("Python", "BI", "PowerBI"),   0.74, "high", 0.80),
    Candidate(11, "Camila Ponce",     "F", 24, "AR", 2,  "Licenciatura",    ("JavaScript", "Vue", "CSS"),  0.71, "med",  0.70),
    Candidate(12, "Sebastián Mora",   "M", 45, "CO", 18, "Doctorado",       ("C++", "Embedded", "IoT"),    0.78, "med",  0.77),
]


def get(candidate_id: int) -> Candidate:
    for c in CANDIDATES:
        if c.id == candidate_id:
            return c
    raise KeyError(f"no existe candidato id={candidate_id}")
