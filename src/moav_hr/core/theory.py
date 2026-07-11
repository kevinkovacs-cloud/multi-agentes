"""
Teorías de aprendizaje ⟨Si, A, Sf, P, K, U⟩ y su base de conocimiento.

v13 Def. 3 (teoría + equivalencia por cuantización), Def. 4 (selección por ranking).

Equivalencia por cuantización: como en un agente LLM `Si` vive en un espacio de
embeddings continuo, la igualdad exacta tiene probabilidad nula. Dos situaciones son
equivalentes (Si ≅ Si′) si su similitud semántica supera un umbral δ. La función de
similitud se inyecta (default: igualdad exacta, que recupera el caso simbólico/discreto).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
import json

# similitud sobre la serialización de una situación: (a, b) -> [0,1]
SimFn = Callable[[dict, dict], float]


def serialize(situation: dict[str, Any]) -> str:
    """Serializa una situación como JSON canónico (región 1, §2.2)."""
    return json.dumps(situation, ensure_ascii=False, sort_keys=True)


def exact_sim(a: dict, b: dict) -> float:
    return 1.0 if a == b else 0.0


@dataclass
class Theory:
    si: dict[str, Any]           # situación inicial
    a: str                        # acción
    sf: dict[str, Any]           # situación final
    p: int = 0                    # éxitos
    k: int = 0                    # usos
    u: float = 0.0                # utilidad U(t) = acc(t) ∈ [0,1]  (Def. 5)

    def __post_init__(self):
        if self.p > self.k:
            raise ValueError("invariante de Def. 3 violada: P ≤ K")

    @property
    def reliability(self) -> float:
        """
        Confiabilidad con suavizado de Laplace (A2): (P+1)/(K+2).

        Media posterior Beta(1,1) — definida en K=0 (→ 0.5), regulariza teorías con
        pocos usos y converge a P/K cuando K crece. Reemplaza el estimador crudo P/K
        de la Def. 3, que era indefinido en K=0 y sobreconfiado con K chico.
        """
        return (self.p + 1) / (self.k + 2)

    def reinforce(self, success: bool) -> None:
        self.k += 1
        if success:
            self.p += 1

    def to_dict(self) -> dict[str, Any]:
        return {"si": self.si, "a": self.a, "sf": self.sf, "p": self.p,
                "k": self.k, "u": round(self.u, 6),
                "reliability": round(self.reliability, 4)}


def equivalent(a: dict, b: dict, sim: SimFn, delta: float) -> bool:
    """Si ≅ Si′  ⟺  similitud ≥ δ  (Def. 3)."""
    return sim(a, b) >= delta


def theories_equal(t1: Theory, t2: Theory, sim: SimFn, delta: float) -> bool:
    """Iguales: (Si ≅ Si′, A = A′, Sf ≅ Sf′)."""
    return (t1.a == t2.a and equivalent(t1.si, t2.si, sim, delta)
            and equivalent(t1.sf, t2.sf, sim, delta))


def theories_similar(t1: Theory, t2: Theory, sim: SimFn, delta: float) -> bool:
    """Similares: (Si ≅ Si′, A = A′) pero Sf ≉ Sf′."""
    return (t1.a == t2.a and equivalent(t1.si, t2.si, sim, delta)
            and not equivalent(t1.sf, t2.sf, sim, delta))


class TheoryBase:
    """Base de conocimiento de teorías de un agente (θᵢ, Def. 1/2)."""

    def __init__(self, sim: Optional[SimFn] = None, delta: float = 1.0) -> None:
        self.theories: list[Theory] = []
        self.sim: SimFn = sim or exact_sim
        self.delta = delta

    def add(self, theory: Theory) -> None:
        self.theories.append(theory)

    def applicable(self, situation: dict[str, Any]) -> list[Theory]:
        """Teorías cuya Si es equivalente a la situación dada (Def. 3/4)."""
        return [t for t in self.theories
                if equivalent(t.si, situation, self.sim, self.delta)]

    def select(self, situation: dict[str, Any]) -> Optional[Theory]:
        """Def. 4: argmax por orden lexicográfico (U desc, P desc, K asc)."""
        cands = self.applicable(situation)
        if not cands:
            return None
        cands.sort(key=lambda t: (-t.u, -t.p, t.k))
        return cands[0]

    def find_equal(self, theory: Theory) -> Optional[Theory]:
        for t in self.theories:
            if theories_equal(t, theory, self.sim, self.delta):
                return t
        return None

    def find_similar(self, theory: Theory) -> Optional[Theory]:
        for t in self.theories:
            if theories_similar(t, theory, self.sim, self.delta):
                return t
        return None

    def __len__(self) -> int:
        return len(self.theories)

    def to_json(self) -> str:
        return json.dumps([t.to_dict() for t in self.theories],
                          ensure_ascii=False, indent=2)
