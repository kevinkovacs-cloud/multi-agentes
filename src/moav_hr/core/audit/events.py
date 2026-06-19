"""Tipos de evento de auditoría (v13 §2.5 — subclases de EventoDeAuditoría)."""
from __future__ import annotations
from enum import Enum


class EventType(str, Enum):
    DECISION = "EventoDecision"
    ESCALAMIENTO = "EventoEscalamiento"
    TRANSFERENCIA = "EventoTransferencia"
    BLOQUEO_EQUIDAD = "EventoBloqueoPorEquidad"
    # genéricos del recorrido por regiones (no son subclases de §2.5, sólo telemetría)
    REGION = "EventoRegion"
