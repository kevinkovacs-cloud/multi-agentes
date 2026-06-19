"""
Ciclo de vida del agente: estados de evolución, capas de operadores y las 7 regiones.

v13 §2.1 (capas BIO/TBO/WIO como fases), Def. 2 (estado y capa activa), §3 (7 regiones).
El orden Born ≺ Novato ≺ Trained ≺ Mature es TOTAL (axioma de §2.5 / Def. 8).
"""
from __future__ import annotations
from enum import Enum, IntEnum


class MaturityState(IntEnum):
    """Estados de evolución (orden total por el valor entero)."""
    BORN = 0
    NOVATO = 1
    TRAINED = 2
    MATURE = 3

    @property
    def label(self) -> str:
        return self.name.lower()


class Layer(str, Enum):
    BIO = "BIO"   # operadores implantados (diseñador)
    TBO = "TBO"   # operadores entrenados (fine-tuning/RLHF)
    WIO = "WIO"   # operadores de interacción con el mundo (online)


class Region(IntEnum):
    """Las 7 regiones de tareas del LLC por ciclo percepción-acción (§3)."""
    SITUATION_INIT = 1   # construir Si
    ACTION = 2           # ejecutar A (RAG + few-shot)
    SITUATION_FINAL = 3  # registrar Sf
    UTILITY = 4          # U(t) + Monitor evalúa fair(W)/U_op(W)
    LEARNING = 5         # ponderar P,K y registrar teoría
    STATISTICS = 6       # estadísticas de aprendizaje
    EVOLUTION = 7        # evolución del agente (gated por equidad)


# capa activa y capas acumuladas por estado (§2.1)
_ACTIVE = {
    MaturityState.BORN: Layer.BIO,
    MaturityState.NOVATO: Layer.TBO,
    MaturityState.TRAINED: Layer.TBO,
    MaturityState.MATURE: Layer.WIO,
}
_CUMULATIVE = {
    MaturityState.BORN: "BIO",
    MaturityState.NOVATO: "BIO+TBO",
    MaturityState.TRAINED: "BIO+TBO",
    MaturityState.MATURE: "BIO+TBO+WIO",
}


def active_layer(state: MaturityState) -> Layer:
    return _ACTIVE[state]


def layers_active(state: MaturityState) -> str:
    return _CUMULATIVE[state]


def next_state(state: MaturityState) -> MaturityState:
    """Avance monótono de un estado al siguiente (tope en MATURE)."""
    return MaturityState(min(int(state) + 1, int(MaturityState.MATURE)))
