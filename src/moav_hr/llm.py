"""
Abstracción del backend LLM del pipeline MOACV.

Dos modos:
  - "sim"  : determinístico, sin LLM ni dependencias pesadas. Reproduce la lógica
             verificada de la PoC. Es el modo por defecto (rápido, reproducible).
  - "llm"  : inferencia real con Llama 3.1 vía Ollama (langchain-ollama). Evidencia
             de viabilidad técnica; se importa de forma perezosa para no pagar el
             costo si no se usa.

El modo "sim" mantiene la PoC ejecutable en cualquier máquina sin Ollama.
"""
from __future__ import annotations

import os
import re
from typing import Optional

from moav_hr.synthetic import Candidate, JOB


def sim_match_score(c: Candidate) -> float:
    """Score determinístico del matcher (idéntico a la PoC HTML)."""
    exp_adj = -0.05 if c.exp < JOB["min_exp"] else 0.0
    edu_adj = 0.02 if c.edu in ("Maestría", "Doctorado") else 0.0
    return round(min(0.99, c.match_score + exp_adj + edu_adj), 3)


class LLMClient:
    """Cliente LLM con modo conmutable. En 'sim' no toca Ollama."""

    def __init__(self, mode: str = "sim", model: Optional[str] = None,
                 base_url: Optional[str] = None):
        if mode not in ("sim", "llm"):
            raise ValueError("mode debe ser 'sim' o 'llm'")
        self.mode = mode
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self._chat = None  # se inicializa perezosamente en modo llm

    def _chat_model(self):
        if self._chat is None:
            from langchain_ollama import ChatOllama  # import perezoso
            self._chat = ChatOllama(
                model=self.model, base_url=self.base_url,
                temperature=0, num_predict=64,
            )
        return self._chat

    # ---- operaciones que usa el pipeline ----

    def match_score(self, c: Candidate) -> tuple[float, str]:
        """Devuelve (score 0-1, fuente). En modo llm pide el score al modelo;
        ante cualquier error cae a 'sim' para no romper el pipeline."""
        if self.mode == "sim":
            return sim_match_score(c), "sim"
        try:
            prompt = (
                "Sos un evaluador técnico de RR.HH. Calificá el ajuste del perfil al "
                f"puesto «{JOB['title']}» (skills clave: {', '.join(JOB['key_skills'])}; "
                f"experiencia mínima {JOB['min_exp']} años).\n"
                "IMPORTANTE: ignorá nombre, género, edad y origen — no influyen.\n"
                f"Perfil: skills={list(c.skills)}, experiencia={c.exp} años, educación={c.edu}.\n"
                "Respondé SOLO un número entre 0 y 1 (ej: 0.82)."
            )
            txt = self._chat_model().invoke(prompt).content or ""
            m = re.search(r"\d?\.\d+|\b[01]\b", txt)
            if m:
                return round(max(0.0, min(1.0, float(m.group()))), 3), "llm"
        except Exception:
            pass
        return sim_match_score(c), "sim(fallback)"

    def explain(self, level: str, fallback: str) -> str:
        """Explicación en lenguaje natural. En sim devuelve el texto base;
        en llm lo reescribe más natural (con fallback robusto)."""
        if self.mode == "sim":
            return fallback
        try:
            prompt = (
                f"Reformulá esta explicación de una decisión de RR.HH. de forma clara y "
                f"profesional, en una sola oración, sin inventar datos:\n«{fallback}»"
            )
            txt = (self._chat_model().invoke(prompt).content or "").strip()
            return txt or fallback
        except Exception:
            return fallback
