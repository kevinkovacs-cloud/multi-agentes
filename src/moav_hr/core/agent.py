"""
Agente genérico del modelo (Def. 2: aᵢ = ⟨θᵢ, sᵢ, Lᵢ⟩).

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
        # identidad de teorías por CUANTIZACIÓN (q_canonical, Def. 3/A1); la similitud
        # continua y su umbral `delta` son SOLO de recuperación (retrieval, §2.2)
        self.theories = TheoryBase()
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
    def learn(self, si: dict, a: str, sf: dict, success: bool,
              u: Optional[float] = None) -> Theory:
        """Registra/refuerza una teoría. Si no se pasa `u`, U := reliability (Laplace, A2)."""
        cand = Theory(si=si, a=a, sf=sf)
        existing = self.theories.find_equal(cand)
        if existing is not None:
            existing.reinforce(success)
            existing.u = u if u is not None else existing.reliability
            return existing
        cand.reinforce(success)
        cand.u = u if u is not None else cand.reliability
        self.theories.add(cand)
        return cand

    # ---- reputación de equidad (Def. 9) ----
    def record_window_fairness(self, fair_w: float) -> None:
        self._fair_history.append(fair_w)

    @property
    def windows_observed(self) -> int:
        """Cantidad de ventanas de equidad observadas (historia real, A9)."""
        return len(self._fair_history)

    def reputation(self, m: int = 5, r0: Optional[float] = None) -> float:
        """
        rⱼ = promedio de fair(W) en las últimas m ventanas (Def. 9).

        Arranque en frío (A9): sin historia devuelve el prior r0 (default 0.8 — el τ_r
        del Monitor, DECLARADO como prior, no evidencia). Antes devolvía 1.0: un agente
        recién nacido lucía con reputación perfecta. El prior habilita recibir; DONAR
        exige además historia mínima (ver can_donate — regla asimétrica).
        """
        if not self._fair_history:
            return r0 if r0 is not None else 0.8
        last = self._fair_history[-m:]
        return round(sum(last) / len(last), 4)

    def can_donate(self, m0: int = 3) -> bool:
        """Historia mínima para DONAR conocimiento (A9): ≥ m0 ventanas observadas.
        Recibir no exige historia; aportar sí."""
        return self.windows_observed >= m0

    # ---- compartición (Def. 7, 8) condicionada por reputación (Def. 9) ----
    def transfer_to(self, apprentice: "MOACVAgent", tau: float = 0.0,
                    m0: int = 3) -> ShareReport:
        """Colaboración maestro→aprendiz (Def. 8): requiere mismo rol, nivel
        estrictamente superior y — A9 — historia mínima del donante."""
        if self.role != apprentice.role:
            raise ValueError(f"colaboración inválida: roles distintos ({self.role}→{apprentice.role})")
        if int(self.maturity) <= int(apprentice.maturity):
            raise ValueError("el colaborador debe tener nivel estrictamente superior (Def. 8)")
        if not self.can_donate(m0):
            raise ValueError(f"el donante no puede aportar sin historia de equidad "
                             f"(A9: requiere ≥{m0} ventanas, tiene {self.windows_observed})")
        return collaborate(apprentice.theories, self.theories,
                           donor_reputation=self.reputation(), tau=tau)

    def cooperate_with(self, peer: "MOACVAgent", tau: float = 0.0,
                       m0: int = 3) -> ShareReport:
        """Cooperación entre pares (Def. 7): mismo rol, mismo estado de evolución;
        el donante (peer, cuya reputación gatea la fusión) exige historia mínima (A9)."""
        if self.role != peer.role:
            raise ValueError("cooperación inválida: roles distintos")
        if self.maturity != peer.maturity:
            raise ValueError("la cooperación requiere mismo estado de evolución (Def. 7)")
        if not peer.can_donate(m0):
            raise ValueError(f"el donante no puede aportar sin historia de equidad "
                             f"(A9: requiere ≥{m0} ventanas, tiene {peer.windows_observed})")
        return cooperate(self.theories, peer.theories,
                         donor_reputation=peer.reputation(), tau=tau)

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
