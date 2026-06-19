"""
Recuperación de teorías por similitud (RAG sobre la base de teorías) — v13 §2.2.

Flujo (P2.1): serializar Si (JSON) → similitud sobre la base → filtrar por umbral δ
(equivalencia por cuantización, Def. 3) → top-k por ranking de utilidad (Def. 4) →
formatear como few-shot para inyectar en el prompt del LLM.

Similitud: cosine sobre bag-of-words de la serialización (determinística, sin modelo).
Es un proxy liviano de la similitud semántica; el upgrade a embeddings (Ollama /
sentence-transformers) es directo cambiando `similarity`.
"""
from __future__ import annotations
import math
from collections import Counter

from moav_hr.core.theory import Theory, TheoryBase, serialize


def _kv_tokens(situation: dict) -> Counter:
    """Tokens atómicos clave=valor (no se parte el valor): discrimina por atributo."""
    return Counter(f"{k}={situation[k]}" for k in situation)


def similarity(a: dict, b: dict) -> float:
    """Cosine sobre tokens clave=valor. Inyectable en TheoryBase como sim_fn (equivalencia Def. 3)."""
    ca, cb = _kv_tokens(a), _kv_tokens(b)
    common = set(ca) & set(cb)
    if not ca or not cb:
        return 0.0
    num = sum(ca[t] * cb[t] for t in common)
    na = math.sqrt(sum(v * v for v in ca.values()))
    nb = math.sqrt(sum(v * v for v in cb.values()))
    return num / (na * nb) if na and nb else 0.0


class TheoryRetriever:
    """Recupera las top-k teorías relevantes para una situación (§2.2)."""

    def __init__(self, base: TheoryBase, delta: float = 0.6, top_k: int = 3):
        self.base = base
        self.delta = delta
        self.top_k = top_k

    def retrieve(self, situation: dict) -> list[Theory]:
        scored = [(similarity(situation, t.si), t) for t in self.base.theories]
        near = [(s, t) for s, t in scored if s >= self.delta]      # cuantización Def. 3
        near.sort(key=lambda st: (-st[1].u, -st[1].p, st[1].k))    # ranking Def. 4
        return [t for _, t in near[: self.top_k]]

    @staticmethod
    def few_shot(theories: list[Theory]) -> str:
        """Formatea las teorías recuperadas como contexto few-shot para el prompt."""
        if not theories:
            return ""
        lines = ["Decisiones previas relevantes (situación → acción exitosa · evidencia P/K):"]
        for t in theories:
            lines.append(f"- {serialize(t.si)} → {t.a}  (P/K={t.p}/{t.k}, U={t.u:.2f})")
        return "\n".join(lines)
