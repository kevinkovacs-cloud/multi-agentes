"""
Modelo de teorías de aprendizaje del LLC (Learning Life Cycle).

Cada agente registra su experiencia como teorías, siguiendo la formalización
del modelo de ciclo de vida LLC (Learning Life Cycle, UNLP 2010):

    Teoría = ⟨Si, A, Sf, P, K, U⟩

reinterpretada para agentes LLM en contextos de decisión social sensible.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
import json


@dataclass
class Theory:
    """
    Una teoría es una unidad de conocimiento del agente.

    Si : situación inicial — el contexto de evaluación (ej: perfil + puesto).
    A  : acción — la decisión tomada por el agente.
    Sf : situación final — el resultado validado de la acción.
    P  : cantidad de veces que la teoría se cumplió (éxitos).
    K  : cantidad de veces que se usó la teoría (usos).
    U  : función de utilidad — pondera precisión predictiva y equidad.
    """
    si: dict[str, Any]          # situación inicial
    a: str                       # acción
    sf: dict[str, Any]          # situación final
    p: int = 0                   # éxitos
    k: int = 0                   # usos
    u: float = 0.0               # utilidad

    @property
    def reliability(self) -> float:
        """Confiabilidad P/K (1 = confiable, 0 = no confiable)."""
        return self.p / self.k if self.k > 0 else 0.0

    def reinforce(self, success: bool) -> None:
        """
        Refuerza o debilita la teoría según el resultado.
        Éxito: incrementa P y K. Fracaso: incrementa solo K (debilita P/K).
        """
        self.k += 1
        if success:
            self.p += 1

    def matches(self, situation: dict[str, Any], action: Optional[str] = None) -> bool:
        """Determina si esta teoría aplica a una situación (y opcionalmente acción)."""
        same_si = self.si == situation
        return same_si and (action is None or self.a == action)

    def to_dict(self) -> dict[str, Any]:
        return {
            "si": self.si, "a": self.a, "sf": self.sf,
            "p": self.p, "k": self.k, "u": round(self.u, 6),
            "reliability": round(self.reliability, 4),
        }


class TheoryBase:
    """
    Base de conocimiento de teorías de un agente.

    Implementa la selección de teoría por ranking (planificador del LLC):
    se ordena por mayor U; ante empate, mayor P; luego menor K.
    """

    def __init__(self) -> None:
        self.theories: list[Theory] = []

    def add(self, theory: Theory) -> None:
        self.theories.append(theory)

    def select(self, situation: dict[str, Any]) -> Optional[Theory]:
        """
        Selecciona la mejor teoría aplicable a la situación actual.
        Criterio de ranking del LLC: mayor U, luego mayor P, luego menor K.
        """
        candidates = [t for t in self.theories if t.matches(situation)]
        if not candidates:
            return None
        candidates.sort(key=lambda t: (-t.u, -t.p, t.k))
        return candidates[0]

    def find_equal(self, theory: Theory) -> Optional[Theory]:
        """Busca una teoría igual (misma Si, A, Sf)."""
        for t in self.theories:
            if t.si == theory.si and t.a == theory.a and t.sf == theory.sf:
                return t
        return None

    def find_similar(self, theory: Theory) -> Optional[Theory]:
        """Busca una teoría similar (misma Si y A, distinto Sf)."""
        for t in self.theories:
            if t.si == theory.si and t.a == theory.a and t.sf != theory.sf:
                return t
        return None

    def __len__(self) -> int:
        return len(self.theories)

    def to_json(self) -> str:
        return json.dumps([t.to_dict() for t in self.theories], ensure_ascii=False, indent=2)


def collaborate(receptor: TheoryBase, colaborador: TheoryBase) -> TheoryBase:
    """
    Mecanismo de colaboración maestro→aprendiz del LLC.

    Un agente colaborador (Mature) transfiere su experiencia a un agente
    receptor (Novato) del mismo rol:
      - Si la teoría existe igual en el receptor: se refuerza (suma P y K).
      - Si existe una teoría similar: se debilita (suma solo K, mantiene P).
      - Si no existe ni igual ni similar: se transfiere tal cual.

    Reproduce el algoritmo de colaboración del modelo LLC original
    (UNLP, 2010 — "Colaboración entre SARs").
    """
    for theory in colaborador.theories:
        equal = receptor.find_equal(theory)
        if equal is not None:
            equal.p += theory.p
            equal.k += theory.k
            continue

        similar = receptor.find_similar(theory)
        if similar is not None:
            # se debilita: suma K sin sumar P
            similar.k += theory.k
            continue

        # no existe: se transfiere tal cual
        receptor.add(Theory(
            si=theory.si, a=theory.a, sf=theory.sf,
            p=theory.p, k=theory.k, u=theory.u,
        ))
    return receptor
