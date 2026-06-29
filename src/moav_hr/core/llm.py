"""
Backend LLM genérico del modelo.

Modo `sim` (determinístico, sin LLM — el dominio computa la salida) o `llm`
(inferencia real con Llama 3.1 vía Ollama, import perezoso). El núcleo no conoce
el dominio: la lógica de `sim` vive en la instancia (p. ej. instances/hr/scoring.py).
"""
from __future__ import annotations
import os
from typing import Optional


class LLMBackend:
    def __init__(self, mode: str = "sim", model: Optional[str] = None,
                 base_url: Optional[str] = None):
        if mode not in ("sim", "llm"):
            raise ValueError("mode debe ser 'sim' o 'llm'")
        self.mode = mode
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self._chat = None

    def _chat_model(self):
        if self._chat is None:
            from langchain_ollama import ChatOllama
            self._chat = ChatOllama(model=self.model, base_url=self.base_url,
                                    temperature=0, num_predict=64)
        return self._chat

    def complete(self, prompt: str) -> str:
        """Inferencia real (solo modo llm). Devuelve '' ante error, para no romper el pipeline."""
        if self.mode != "llm":
            raise RuntimeError("complete() no disponible en modo sim")
        try:
            return (self._chat_model().invoke(prompt).content or "").strip()
        except Exception:
            return ""
