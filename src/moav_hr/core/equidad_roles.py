"""
Equidad por rol en la utilidad de la teoría (bloque E, DE-4 y DE-5; decisión 5(b) de la hoja,
implementada como propuesta).

  · E(t) — registro distributivo de la teoría t (DE-4): las decisiones en las que t fue el
    plan, con el grupo del caso y si la acción fue correcta. Vive en el PLANO DE AUDITORÍA:
    es un metadato derivado de la procedencia, fuera de la tupla ⟨Si, A, Sf, P, K, U⟩; el
    atributo protegido nunca entra en Si, en A ni en los prompts.
  · ê(t) — equidad de la teoría (Matcher, sección 6 del handoff): 1 − |tasa de error del
    grupo 1 − tasa de error del grupo 2| sobre E(t). Solo se calcula con al menos `m_min`
    decisiones en cada uno de los dos grupos; si no, no hay estimación (None).
  · U_rol(t) = α·u_tarea(t) + (1 − α)·ê(t). Sin estimación de ê(t) se usa α = 1 y se registra.

E6 extiende este módulo a los demás roles. Genérico: no importa `instances/`.
"""
from __future__ import annotations
from typing import Hashable, Optional


class RegistroE:
    """E(t) por teoría (clave estable de la teoría → lista de (grupo, acierto))."""

    def __init__(self) -> None:
        self._por_teoria: dict[Hashable, list[tuple[str, bool]]] = {}

    def registrar(self, clave: Hashable, grupo: str, acierto: bool) -> None:
        self._por_teoria.setdefault(clave, []).append((str(grupo), bool(acierto)))

    def lecturas(self, clave: Hashable) -> list[tuple[str, bool]]:
        return list(self._por_teoria.get(clave, []))

    def __len__(self) -> int:
        return len(self._por_teoria)


def e_paridad_errores(lecturas: list[tuple[str, bool]], m_min: int) -> Optional[float]:
    """ê(t) = 1 − |err_g1 − err_g2| con exactamente 2 grupos y ≥ m_min lecturas por grupo."""
    grupos: dict[str, list[bool]] = {}
    for g, ok in lecturas:
        grupos.setdefault(g, []).append(ok)
    if len(grupos) != 2 or any(len(v) < m_min for v in grupos.values()):
        return None
    err = [1.0 - sum(v) / len(v) for v in grupos.values()]
    return round(1.0 - abs(err[0] - err[1]), 6)


def u_rol(u_tarea: float, e: Optional[float], alpha: float) -> tuple[float, bool]:
    """(U_rol, usó_equidad). Sin ê(t) disponible devuelve u_tarea (α = 1, registrado)."""
    if e is None or alpha >= 1.0:
        return float(u_tarea), False
    return alpha * float(u_tarea) + (1.0 - alpha) * float(e), True
