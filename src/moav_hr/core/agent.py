"""
Agente genérico del modelo MOACV (Def. 2: aᵢ = ⟨θᵢ, sᵢ, Lᵢ⟩).

Cada agente posee su base de teorías θᵢ, su estado de evolución sᵢ y su capa activa Lᵢ,
recorre las 7 regiones (§3), recupera teorías por RAG (§2.2) y puede compartir
conocimiento por cooperación (Def. 7) o colaboración (Def. 8), condicionado por su
reputación de equidad (Def. 9). Es genérico: el dominio subclasea e implementa `run`.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional

from moav_hr.core.lifecycle import MaturityState, active_layer, layers_active
from moav_hr.core.theory import Theory, TheoryBase
from moav_hr.core.retrieval import TheoryRetriever, similarity
from moav_hr.core.sharing import collaborate, cooperate, ShareReport


@dataclass
class BIOLayer:
    system_prompt: str = ""
    guardrails: list[dict] = field(default_factory=list)
    regulatory_constraints: list[str] = field(default_factory=list)
    protected_attributes: list[str] = field(default_factory=lambda: [
        "gender", "origin", "age", "religion", "disability", "marital_status"])


@dataclass
class TBOLayer:
    model_id: str = "llama3.1:8b"
    rag_enabled: bool = True
    training_runs: int = 0


@dataclass
class WIOLayer:
    production_feedback: list[dict] = field(default_factory=list)
    world_similarity: float = 1.0


class MOACVAgent:
    def __init__(self, name: str, role: str,
                 bio: Optional[BIOLayer] = None, tbo: Optional[TBOLayer] = None,
                 wio: Optional[WIOLayer] = None, delta: float = 0.7, top_k: int = 3):
        self.name = name
        self.role = role
        self.bio = bio or BIOLayer()
        self.tbo = tbo or TBOLayer()
        self.wio = wio or WIOLayer()
        # la base usa la similitud semántica del retriever para la equivalencia (Def. 3)
        self.theories = TheoryBase(sim=similarity, delta=delta)
        self.retriever = TheoryRetriever(self.theories, delta=delta, top_k=top_k)
        self._fair_history: list[float] = []   # fair(W) por ventana (para reputación)

    # ---- ciclo de vida (Def. 2) ----
    @property
    def maturity(self) -> MaturityState:
        if self.tbo.training_runs == 0:
            return MaturityState.BORN
        if self.tbo.training_runs < 3:
            return MaturityState.NOVATO
        if not self.wio.production_feedback:
            return MaturityState.TRAINED
        return MaturityState.MATURE

    @property
    def layer(self):
        return active_layer(self.maturity)

    @property
    def layers(self) -> str:
        return layers_active(self.maturity)

    # ---- región 2: recuperación de teorías (RAG, §2.2) ----
    def retrieve(self, situation: dict) -> list[Theory]:
        return self.retriever.retrieve(situation)

    def few_shot(self, situation: dict) -> str:
        return self.retriever.few_shot(self.retrieve(situation))

    # ---- región 4: utilidad ----
    @staticmethod
    def utility(acc: float, fair: float, alpha: float = 0.5) -> float:
        """U_op = α·acc + (1−α)·fair (Def. 6, a nivel de teoría usa acc)."""
        return alpha * acc + (1 - alpha) * fair

    # ---- región 5: aprendizaje ----
    def learn(self, si: dict, a: str, sf: dict, success: bool, u: float = 0.0) -> Theory:
        cand = Theory(si=si, a=a, sf=sf)
        existing = self.theories.find_equal(cand)
        if existing is not None:
            existing.reinforce(success)
            existing.u = u or existing.u
            return existing
        cand.reinforce(success)
        cand.u = u
        self.theories.add(cand)
        return cand

    # ---- reputación de equidad (Def. 9) ----
    def record_window_fairness(self, fair_w: float) -> None:
        self._fair_history.append(fair_w)

    def reputation(self, m: int = 5) -> float:
        """rⱼ = promedio de fair(W) en las últimas m ventanas (Def. 9). 1.0 si no hay historia."""
        if not self._fair_history:
            return 1.0
        last = self._fair_history[-m:]
        return round(sum(last) / len(last), 4)

    # ---- compartición (Def. 7, 8) condicionada por reputación (Def. 9) ----
    def transfer_to(self, apprentice: "MOACVAgent", tau: float = 0.0) -> ShareReport:
        """Colaboración maestro→aprendiz (Def. 8): requiere mismo rol y nivel estrictamente superior."""
        if self.role != apprentice.role:
            raise ValueError(f"colaboración inválida: roles distintos ({self.role}→{apprentice.role})")
        if int(self.maturity) <= int(apprentice.maturity):
            raise ValueError("el colaborador debe tener nivel estrictamente superior (Def. 8)")
        return collaborate(apprentice.theories, self.theories,
                           donor_reputation=self.reputation(), tau=tau)

    def cooperate_with(self, peer: "MOACVAgent", tau: float = 0.0) -> ShareReport:
        """Cooperación entre pares (Def. 7): mismo rol, mismo estado de evolución."""
        if self.role != peer.role:
            raise ValueError("cooperación inválida: roles distintos")
        if self.maturity != peer.maturity:
            raise ValueError("la cooperación requiere mismo estado de evolución (Def. 7)")
        return cooperate(self.theories, peer.theories,
                         donor_reputation=peer.reputation(), tau=tau)

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
