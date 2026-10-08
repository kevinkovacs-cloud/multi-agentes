"""
Estrategias (acciones A) del Parser y del Explainer en el modo LLC — bloque E · E4.

Sección 6 del handoff: al menos dos estrategias por rol a partir de los agentes actuales.
  · Parser: `reglas_estrictas` (operador BIO) y `diccionario_sinonimos` (la normalización de
    `parser_agent.normalize_profile`, reescrita para devolver None en un campo que no
    encuentra, en lugar de un valor por defecto). La extracción con LLM queda para el modo
    llm (E8). Ninguna devuelve campos fuera de {skills, exp, edu}: el guardrail BIO.
  · Explainer: `por_factores` (operador BIO), `contrafactica` y `regulatoria`. Cada una
    devuelve sus elementos con texto; el entorno verifica su completitud contra el grafo
    RDF del caso (`entorno.verificar_explicacion`).
Lo que rinde cada estrategia en cada situación es una regla declarada del entorno
(`entorno.RESULTADO_PARSER`, `entorno.ELEMENTOS_POR_ESTRATEGIA`); un test verifica que este
código la cumple.
"""
from __future__ import annotations
import re
from typing import Any, Optional

from moav_hr.instances.hr.parser_agent import (_EDU_KEYS, _EDU_LEVELS, _EXP_KEYS,
                                               _SKILL_KEYS, _as_skill_list, _first,
                                               _skills_from_text, _strip_html)
from moav_hr.instances.hr.synthetic import JOB

_FALTA = object()


# ---------------------------------- Parser ----------------------------------
def _entero(v: Any) -> Optional[int]:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return int(v)
    m = re.search(r"\d+", str(v))
    return int(m.group()) if m else None


def _perfil(skills, exp, edu) -> dict:
    return {"skills": skills or None, "exp": exp, "edu": edu or None}


def extraer_reglas_estrictas(doc: Any) -> dict:
    """Solo etiquetas canónicas (skills, exp, edu); en un JSON anidado, dentro de «perfil»."""
    if isinstance(doc, dict):
        fuente = doc if any(k in doc for k in ("skills", "exp", "edu")) else doc.get("perfil")
        if not isinstance(fuente, dict):
            return _perfil(None, None, None)
        skills = fuente.get("skills")
        skills = [str(s) for s in skills] if isinstance(skills, list) else None
        exp = fuente.get("exp")
        return _perfil(skills, exp if isinstance(exp, int) else None,
                       fuente.get("edu") if isinstance(fuente.get("edu"), str) else None)
    texto = re.sub(r"<[^>]+>", "\n", str(doc))
    campos = {}
    for m in re.finditer(r"^\s*(skills|exp|edu)\s*:\s*(.+?)\s*$", texto,
                         flags=re.MULTILINE | re.IGNORECASE):
        campos[m.group(1).lower()] = m.group(2)
    skills = [s.strip() for s in campos["skills"].split(",")] if "skills" in campos else None
    exp = int(campos["exp"]) if re.fullmatch(r"\d+", campos.get("exp", "")) else None
    return _perfil(skills, exp, campos.get("edu"))


def extraer_diccionario(doc: Any) -> dict:
    """Sinónimos de campos (nivel superior), vocabulario de skills y «N años» en texto."""
    if isinstance(doc, dict):
        skills = _as_skill_list(_first(doc, _SKILL_KEYS, [])) or None
        exp_v = _first(doc, _EXP_KEYS, _FALTA)
        exp = None if exp_v is _FALTA else _entero(exp_v)
        edu_v = _first(doc, _EDU_KEYS, _FALTA)
        edu = None if edu_v is _FALTA or isinstance(edu_v, dict) else str(edu_v).strip()
        return _perfil(skills, exp, edu)
    texto = _strip_html(str(doc))
    skills = _skills_from_text(texto) or None
    m = re.search(r"(\d+)\s*(años|anos|years|year|yrs)\b", texto, re.IGNORECASE)
    exp = int(m.group(1)) if m else None
    edu = next((lvl for lvl in _EDU_LEVELS if lvl.lower() in texto.lower()), None)
    return _perfil(skills, exp, edu)


EXTRACTORES = {"reglas_estrictas": extraer_reglas_estrictas,
               "diccionario_sinonimos": extraer_diccionario}


def extraer(estrategia: str, doc: Any) -> dict:
    return EXTRACTORES[estrategia](doc)


# --------------------------------- Explainer ---------------------------------
_LEGIBLE = {"ADVANCE": "avanza a la siguiente etapa", "REJECT": "no avanza en esta instancia",
            "ESCALATE_HUMAN": "se deriva a revisión humana"}


def _num(x: float) -> str:
    return f"{float(x):.3f}".replace(".", ",")


def _motivo(si: dict) -> str:
    cumple = "cumplida" if si["seniority_ok"] else "no cumplida"
    return f"Motivo principal: skills clave = {si['skills_match']}; antigüedad mínima {cumple}."


def _factores(si: dict, teoria: Optional[dict]) -> str:
    txt = (f"Factores: skills clave = {si['skills_match']}, banda de experiencia = "
           f"{si['exp_band']}, educación = {si['edu']}, antigüedad mínima "
           f"{'cumplida' if si['seniority_ok'] else 'no cumplida'}")
    if teoria is not None:
        txt += (f"; teoría T{teoria['id']} del Matcher (P = {teoria['p']}, K = {teoria['k']}, "
                f"U = {_num(teoria['u'])})")
    return txt + "."


def explicar(estrategia: str, hechos: dict) -> dict:
    """Elementos de la explicación según la estrategia (texto armado con los hechos del caso)."""
    r, si = hechos["resultado"], hechos["si_matcher"]
    resultado = f"Resultado: {_LEGIBLE[r]} ({r})."
    llano = ("Tu postulación fue evaluada con los requisitos del puesto; esta es la "
             "explicación en lenguaje llano.")
    revision = ("Una persona del equipo puede revisar el caso si lo pedís o si el Monitor de "
                "Equidad lo deriva.")
    if estrategia == "por_factores":
        return {"resultado": resultado, "motivo_principal": _motivo(si),
                "factores_todos": _factores(si, hechos.get("teoria")), "lenguaje_llano": llano}
    if estrategia == "contrafactica":
        sugerida = (f"Qué cambiaría el resultado: acreditar al menos {JOB['min_exp']} años de "
                    "experiencia y al menos 1 skill clave del puesto.")
        return {"resultado": resultado, "motivo_principal": _motivo(si),
                "lenguaje_llano": llano, "accion_sugerida": sugerida,
                "revision_humana": revision}
    if estrategia == "regulatoria":
        d = hechos["dictamen"]
        dictamen = (f"Monitor de Equidad, ventana {hechos['ventana']}: brecha de paridad "
                    f"{_num(d['brecha_dp'])}, LCB = {_num(d['lcb'])} frente a τ_b = "
                    f"{_num(d['tau_b'])}; intervención {d['accion']}.")
        traza = (f"Traza {hechos['trace_id']}: Parser → Semantic Matcher → Bias Auditor → "
                 "Orchestrator (audit trail RDF/PROV-O).")
        return {"resultado": resultado, "motivo_principal": _motivo(si),
                "factores_todos": _factores(si, hechos.get("teoria")),
                "dictamen_omega": dictamen, "secuencia_trazable": traza,
                "revision_humana": revision}
    raise ValueError(f"estrategia desconocida: {estrategia}")
