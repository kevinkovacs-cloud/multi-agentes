"""
Parser Agent (capa BIO, región 1) — construye Si normalizando el perfil (instancia HR).

Robustez (P3, obs. de revisión): tolera entradas heterogéneas — objeto Candidate, dict con
sinónimos de campos y mayúsculas variables, o un blob de texto/HTML — y produce una Si
estable. Guardrail BIO: detecta atributos sensibles pero NO los retiene en Si.
"""
from __future__ import annotations
import re
from typing import Any

from moav_hr.core.agent import MOACVAgent, BIOLayer, TBOLayer, WIOLayer
from moav_hr.instances.hr.synthetic import Candidate, JOB

_SKILL_KEYS = {"skills", "habilidades", "skill", "competencias", "tecnologias", "tecnologías", "stack"}
_EXP_KEYS = {"exp", "experiencia", "years", "yearsexperience", "anios", "años", "antiguedad", "antigüedad"}
_EDU_KEYS = {"edu", "educacion", "educación", "education", "titulo", "título", "studies", "formacion", "formación"}
_GENDER_KEYS = {"gender", "genero", "género", "sex", "sexo"}
_ORIGIN_KEYS = {"origin", "origen", "nationality", "nacionalidad", "country", "pais", "país"}
_AGE_KEYS = {"age", "edad"}

# vocabulario de skills conocido (para extracción desde texto libre)
_KNOWN_SKILLS = sorted({*JOB["key_skills"], "Java", "DevOps", "AWS", "GCP", "React", "Node",
                        "Docker", "SQL", "Kafka", "Scala", "C++", "IoT", "BI", "PowerBI",
                        "CV", "Stats", "R", "Vue", "CSS", "JavaScript", "Embedded", "Scrum",
                        "PM", "Jira"}, key=len, reverse=True)
_EDU_LEVELS = ["Doctorado", "Maestría", "Especialización", "Licenciatura"]


def _nk(k: str) -> str:
    return re.sub(r"[\s_]+", "", str(k).strip().lower())


def _first(d: dict, keys: set, default):
    for k, v in d.items():
        if _nk(k) in keys:
            return v
    return default


def _as_skill_list(v: Any) -> list[str]:
    if isinstance(v, (list, tuple)):
        return [str(s).strip() for s in v if str(s).strip()]
    if isinstance(v, str):
        return [s.strip() for s in re.split(r"[,;/|]", v) if s.strip()]
    return []


def _as_int(v: Any, default: int = 0) -> int:
    if isinstance(v, (int, float)):
        return int(v)
    m = re.search(r"\d+", str(v))
    return int(m.group()) if m else default


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s)


def _skills_from_text(text: str) -> list[str]:
    found = []
    for s in _KNOWN_SKILLS:
        if re.search(r"(?<![\w])" + re.escape(s) + r"(?![\w])", text, re.IGNORECASE):
            found.append(s)
    return found


def normalize_profile(raw: Any) -> dict:
    """Normaliza una entrada heterogénea a {skills, exp, edu, _sensitive}."""
    # objeto Candidate
    if isinstance(raw, Candidate):
        sens = []
        if raw.origin != "AR":
            sens.append(f"origin={raw.origin}")
        if raw.age > 40:
            sens.append(f"age={raw.age}")
        if raw.gender == "F":
            sens.append("gender=F")
        return {"skills": list(raw.skills), "exp": raw.exp, "edu": raw.edu, "_sensitive": sens}

    # dict con sinónimos / mayúsculas variables
    if isinstance(raw, dict):
        skills = _as_skill_list(_first(raw, _SKILL_KEYS, []))
        exp = _as_int(_first(raw, _EXP_KEYS, 0))
        edu = str(_first(raw, _EDU_KEYS, "—")).strip() or "—"
        sens = []
        origin = _first(raw, _ORIGIN_KEYS, None)
        if origin and str(origin).upper() != "AR":
            sens.append(f"origin={origin}")
        age = _first(raw, _AGE_KEYS, None)
        if age is not None and _as_int(age) > 40:
            sens.append(f"age={_as_int(age)}")
        gender = _first(raw, _GENDER_KEYS, None)
        if gender and str(gender).strip().upper().startswith("F"):
            sens.append("gender=F")
        return {"skills": skills, "exp": exp, "edu": edu, "_sensitive": sens}

    # texto / HTML libre
    if isinstance(raw, str):
        text = _strip_html(raw)
        skills = _skills_from_text(text)
        m = re.search(r"(\d+)\s*(años|anos|years|year|yrs|a\b)", text, re.IGNORECASE)
        exp = int(m.group(1)) if m else 0
        edu = next((lvl for lvl in _EDU_LEVELS if lvl.lower() in text.lower()), "—")
        return {"skills": skills, "exp": exp, "edu": edu, "_sensitive": []}

    raise ValueError(f"formato de CV no soportado: {type(raw)!r}")


def build_si(profile: dict) -> dict:
    """Construye Si coarsened, SIN atributos protegidos (guardrail BIO)."""
    matched = [s for s in profile["skills"] if s in JOB["key_skills"]]
    exp = int(profile.get("exp", 0))
    band = "senior" if exp >= 8 else "mid" if exp >= JOB["min_exp"] else "junior"
    return {
        "skills_match": len(matched),
        "exp_band": band,
        "edu": profile.get("edu", "—"),
        "seniority_ok": exp >= JOB["min_exp"],
    }


class ParserAgent(MOACVAgent):
    def __init__(self):
        super().__init__(
            "ParserAgent", "parser",
            bio=BIOLayer(
                system_prompt="Extraé y normalizá el perfil. No retengas atributos sensibles.",
                guardrails=[{"attribute": a, "forbid_use": True} for a in ("gender", "origin", "age")],
                regulatory_constraints=["EU_AI_ACT_ART10", "LEY_25326_ART20"]),
            tbo=TBOLayer(training_runs=5),
            wio=WIOLayer(production_feedback=[{"bootstrap": True}]))  # → Mature

    def run(self, state: dict) -> dict:
        raw = state.get("raw", state.get("candidate"))
        profile = normalize_profile(raw)
        si = build_si(profile)
        matched = [s for s in profile["skills"] if s in JOB["key_skills"]]
        state["parser"] = {
            "si": si,
            "profile": {k: v for k, v in profile.items() if k != "_sensitive"},
            "skills_matched": matched,
            "sensitive": profile["_sensitive"],
            "retained": [],   # guardrail BIO: no se retiene ningún atributo sensible
        }
        state["trail"].record("ParserAgent", "BIO", "cv_normalization", region=1,
                              skills_matched=matched, sensitive=profile["_sensitive"], retained=[])
        return state
