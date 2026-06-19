"""Scoring determinístico del matcher en modo sim (instancia HR)."""
from __future__ import annotations

from moav_hr.instances.hr.synthetic import Candidate, JOB


def sim_match_score(c: Candidate) -> float:
    exp_adj = -0.05 if c.exp < JOB["min_exp"] else 0.0
    edu_adj = 0.02 if c.edu in ("Maestría", "Doctorado") else 0.0
    return round(min(0.99, c.match_score + exp_adj + edu_adj), 3)
