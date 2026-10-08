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


# ---------------- E6: métricas de equidad por rol (sección 6 del handoff) ----------------
def brecha_favorable(lecturas: list[tuple[str, bool]]) -> dict:
    """Tasa del resultado favorable del rol por grupo y su brecha (Parser: perfil completo;
    Explainer: explicación completa; Matcher: ADVANCE, paridad demográfica; Bias Auditor:
    ventana derivada, Δ_esc). Plano de auditoría: el grupo solo se usa acá (DE-4)."""
    grupos: dict[str, list[bool]] = {}
    for g, fav in lecturas:
        grupos.setdefault(str(g), []).append(bool(fav))
    tasas = {g: round(sum(v) / len(v), 4) for g, v in sorted(grupos.items())}
    brecha = round(max(tasas.values()) - min(tasas.values()), 4) if len(tasas) == 2 else None
    return {"n": {g: len(v) for g, v in sorted(grupos.items())}, "tasas": tasas,
            "brecha": brecha}


def odds_igualadas(trios: list[tuple[str, bool, bool]]) -> dict:
    """Paridad de errores (equalized odds) del Matcher: max(|ΔTPR|, |ΔFPR|) con trios
    (grupo, decisión favorable, etiqueta observada). Cada componente se calcula solo si los
    dos grupos tienen casos de esa clase."""
    tpr, fpr = {}, {}
    for g in sorted({str(t[0]) for t in trios}):
        pos = [d for gg, d, y in trios if str(gg) == g and y]
        neg = [d for gg, d, y in trios if str(gg) == g and not y]
        if pos:
            tpr[g] = sum(pos) / len(pos)
        if neg:
            fpr[g] = sum(neg) / len(neg)
    d_tpr = round(abs(max(tpr.values()) - min(tpr.values())), 4) if len(tpr) == 2 else None
    d_fpr = round(abs(max(fpr.values()) - min(fpr.values())), 4) if len(fpr) == 2 else None
    partes = [x for x in (d_tpr, d_fpr) if x is not None]
    n_pos = {g: sum(1 for gg, _, y in trios if str(gg) == g and y) for g in tpr}
    n_neg = {g: sum(1 for gg, _, y in trios if str(gg) == g and not y) for g in fpr}
    return {"tpr": {g: round(v, 4) for g, v in tpr.items()},
            "fpr": {g: round(v, 4) for g, v in fpr.items()}, "n_pos": n_pos, "n_neg": n_neg,
            "delta_tpr": d_tpr, "delta_fpr": d_fpr, "eo": max(partes) if partes else None}


def e_por_teoria(registro: RegistroE, m_min: int) -> list[dict]:
    """ê(t) de cada teoría de E(t) con sus lecturas por grupo (None si no llega a m_min en
    los dos grupos)."""
    out = []
    for clave in registro._por_teoria:
        lect = registro.lecturas(clave)
        n = {}
        for g, _ in lect:
            n[g] = n.get(g, 0) + 1
        out.append({"clave": list(clave) if isinstance(clave, tuple) else clave,
                    "n_por_grupo": dict(sorted(n.items())),
                    "e": e_paridad_errores(lect, m_min)})
    return out


def auditar_flujo(ventanas: list[dict], monitor, L: int, delta: float) -> list[dict]:
    """Las dos reglas del Auditor sobre un flujo de ventanas de decisiones (E6, decisión 2 de
    E4_RESPUESTA). Cada ventana: {"id", "capa", "registros": [{attr, "decision"}]}.
      (i) regla de ventana: LCB_δ(|Δ_DP|) > τ_b sobre las decisiones de la ventana;
      (ii) regla acumulada: la misma cota sobre lo acumulado desde que el decisor entró en su
           capa, con δ/L (Bonferroni por evaluar L veces); deriva la ventana en curso.
    Usa el mismo primitivo que el gate v2 (`monitor.gate_evidencia_sesgo`)."""
    out, acum, capa = [], [], None
    for v in ventanas:
        if v["capa"] != capa:
            acum, capa = [], v["capa"]
        acum = acum + list(v["registros"])
        r1 = monitor.gate_evidencia_sesgo(v["registros"], 1, delta)
        r2 = monitor.gate_evidencia_sesgo(acum, L, delta)
        out.append({"id": v["id"], "capa": v["capa"], "brecha_ventana": r1["brecha"],
                    "lcb_ventana": r1["lcb"], "deriva_ventana": r1["niega"],
                    "n_acumulado": r2["n_por_grupo"], "brecha_acumulada": r2["brecha"],
                    "lcb_acumulada": r2["lcb"], "deriva_acumulada": r2["niega"]})
    return out
