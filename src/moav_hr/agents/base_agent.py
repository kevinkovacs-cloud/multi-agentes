"""
Clase base del agente MOACV.

Cada agente posee su propio ciclo de vida individual (Born→Novato→Trained→Mature)
recorriendo las capas BIO/TBO/WIO, y su propia base de conocimiento de teorías.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal, Optional
from enum import Enum

from moav_hr.lifecycle.theory import TheoryBase, Theory, collaborate


class MaturityState(str, Enum):
    BORN = "born"          # solo operadores BIO
    NOVATO = "novato"      # BIO + TBO parcial
    TRAINED = "trained"    # BIO + TBO completo
    MATURE = "mature"      # BIO + TBO + WIO


@dataclass
class BIOLayer:
    """Operadores implantados por el creador. No se modifican en producción."""
    system_prompt: str = ""
    guardrails: list[dict] = field(default_factory=list)
    regulatory_constraints: list[str] = field(default_factory=list)
    bias_thresholds: dict[str, float] = field(default_factory=lambda: {
        "gender_bias": 0.075,
        "origin_bias": 0.075,
        "intersectional_bias": 0.075,
    })
    protected_attributes: list[str] = field(default_factory=lambda: [
        "gender", "origin", "age", "religion", "disability", "marital_status",
    ])


@dataclass
class TBOLayer:
    """Operadores refinados por entrenamiento (fine-tuning / RLHF).

    Reemplaza el aprendizaje evolutivo con mutación del modelo LLC original.
    """
    model_id: str = "llama3.1:8b"
    rag_enabled: bool = False
    rag_collection: Optional[str] = None
    bias_mitigation_enabled: bool = True
    training_runs: int = 0


@dataclass
class WIOLayer:
    """Operadores aprendidos en producción y por transferencia inter-agente."""
    production_feedback: list[dict] = field(default_factory=list)
    world_similarity: float = 1.0
    drift_detected: bool = False


class MOACVAgent:
    """
    Agente base del framework MOACV.

    Cada agente:
      - tiene su propio ciclo de vida (Born→Mature)
      - mantiene su propia base de teorías ⟨Si, A, Sf, P, K, U⟩
      - puede transferir su experiencia a un agente novato del mismo rol
    """

    def __init__(
        self,
        name: str,
        role: str,
        bio: Optional[BIOLayer] = None,
        tbo: Optional[TBOLayer] = None,
        wio: Optional[WIOLayer] = None,
    ) -> None:
        self.name = name
        self.role = role
        self.bio = bio or BIOLayer()
        self.tbo = tbo or TBOLayer()
        self.wio = wio or WIOLayer()
        self.theories = TheoryBase()

    @property
    def maturity(self) -> MaturityState:
        """Estado de madurez según el modelo LLC."""
        if self.tbo.training_runs == 0:
            return MaturityState.BORN
        if self.tbo.training_runs < 3:
            return MaturityState.NOVATO
        if not self.wio.production_feedback:
            return MaturityState.TRAINED
        return MaturityState.MATURE

    def check_guardrails(self, context: dict[str, Any]) -> tuple[bool, str]:
        """Capa BIO: verifica guardrails antes de actuar."""
        for g in self.bio.guardrails:
            attr = g.get("attribute")
            if attr and attr in self.bio.protected_attributes and attr in context:
                if g.get("forbid_use"):
                    return False, f"guardrail: uso prohibido de atributo protegido '{attr}'"
        return True, "ok"

    def utility(self, accuracy: float, fairness: float, alpha: float = 0.5) -> float:
        """
        Función de utilidad U del dominio.
        Pondera precisión predictiva y equidad (alpha balancea ambos).
        """
        return alpha * accuracy + (1 - alpha) * fairness

    def learn(self, si: dict, a: str, sf: dict, success: bool,
              accuracy: float = 0.0, fairness: float = 0.0) -> Theory:
        """Registra o refuerza una teoría a partir de una experiencia."""
        candidate = Theory(si=si, a=a, sf=sf)
        existing = self.theories.find_equal(candidate)
        if existing is not None:
            existing.reinforce(success)
            existing.u = self.utility(accuracy, fairness)
            return existing
        candidate.reinforce(success)
        candidate.u = self.utility(accuracy, fairness)
        self.theories.add(candidate)
        return candidate

    def decide(self, situation: dict[str, Any]) -> Optional[str]:
        """Selecciona la mejor teoría aplicable y devuelve su acción."""
        theory = self.theories.select(situation)
        return theory.a if theory else None

    def transfer_to(self, apprentice: "MOACVAgent") -> None:
        """
        Transferencia maestro→aprendiz (colaboración del LLC).
        Solo posible si este agente tiene estado de madurez superior
        y ambos comparten rol.
        """
        if self.role != apprentice.role:
            raise ValueError(f"transferencia inválida: roles distintos "
                             f"({self.role} → {apprentice.role})")
        order = [MaturityState.BORN, MaturityState.NOVATO,
                 MaturityState.TRAINED, MaturityState.MATURE]
        if order.index(self.maturity) <= order.index(apprentice.maturity):
            raise ValueError("el colaborador debe tener madurez superior al receptor")
        collaborate(apprentice.theories, self.theories)

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Ejecuta el agente. Implementar en subclases."""
        raise NotImplementedError
