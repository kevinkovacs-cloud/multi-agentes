"""
Planificador por ranking de teorías del LLC (región 2) — bloque E · E2.2 (DE-2, DE-3, P3).

Fuente: Ierache (2010), §4.4.7.2, Fig. 4.21 (p. 107). El planificador ordena las teorías por
mayor U, después mayor P, después menor K, y toma la primera cuya situación inicial coincide
con la situación actual; el plan es esa sola teoría y su acción es la que se ejecuta.

Adaptaciones declaradas:
  · Aplicabilidad = misma celda Q(Si) (cuantización; análogo de la comparación por umbral de
    §4.4.6). Desempate final determinista: recencia desc, id asc.
  · Validez del plan: la primera teoría del orden es plan válido solo si permite «realizar
    una acción con sentido» (p. 106). v1 (P3.1): u_tarea > 0. v2 (pre-registro v2): con U
    basada en la acción, U ≥ 0,5 (la acción no falla más de lo que acierta).
  · «Azar» (Fig. 4.17, p. 101; Alg. 4.5): sin plan válido se recurre al plan por
    contingencia y se cuenta como azar. Ninguna decisión aleatoria sobre personas (DE-3):
    en los escenarios BIO y TBO, la primera acción todavía no probada en la celda, en un
    orden fijo; si ya se probaron todas, el operador BIO. En WIO, el operador BIO. Las capas
    con exploración son configurables por rol (`capas_exploracion`; E5: el Explainer, que
    actúa después de la decisión, explora también en WIO).
  · Respaldo por similitud (DE-2, extensión): solo con la celda vacía y si está activado;
    toma la primera, en el orden de la Fig. 4.21, entre las teorías con similitud ≥ δ y
    u_tarea > 0. Cada uso queda registrado.
  · Fig. 4.21 frente al Alg. 4.7 (P3.2): el Alg. 4.7 (p. 108) desempata por P/K; se registra
    cada vez que los dos órdenes eligen teorías distintas (evidencia para la decisión 2).
  · Equidad (DE-5): con α < 1 el orden usa U_rol = α·u_tarea + (1 − α)·ê(t); la validez
    sigue usando u_tarea.

Genérico: no importa `instances/`.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional

from moav_hr.core.equidad_roles import RegistroE, e_paridad_errores, u_rol
from moav_hr.core.retrieval import similarity
from moav_hr.core.theory import Theory, TheoryBase, theory_key

CAPAS_CON_EXPLORACION = ("BIO", "TBO")


@dataclass
class DecisionPlan:
    accion: str
    motivo: str                       # celda | similitud | azar_no_probada | azar_bio
    teoria: Optional[Theory]
    es_azar: bool
    candidatas: list[dict] = field(default_factory=list)     # orden aplicado (Fig. 4.21)
    validez_aplicada: bool = False    # la primera del orden tenía u_tarea = 0
    desacuerdo_alg47: Optional[dict] = None
    alpha: float = 1.0
    equidad_usada: bool = False       # U_rol usó ê(t) en al menos una candidata


class PlanificadorLLC:
    def __init__(self, base: TheoryBase, acciones: tuple[str, ...],
                 respaldo_similitud: bool = False, delta: float = 0.7,
                 alpha: float = 1.0, registro_e: Optional[RegistroE] = None,
                 m_min: int = 5,
                 similitud: Callable[[dict, dict], float] = similarity,
                 validez_minima: float = 0.0, validez_estricta: bool = True,
                 capas_exploracion: tuple[str, ...] = CAPAS_CON_EXPLORACION):
        self.base = base
        self.capas_exploracion = tuple(capas_exploracion)
        self.acciones = tuple(acciones)
        self.respaldo_similitud = respaldo_similitud
        self.delta = delta
        self.alpha = alpha
        self.registro_e = registro_e
        self.m_min = m_min
        self.similitud = similitud
        # validez del plan: v1 (P3.1) u_tarea > 0 → (0, estricta); v2 (pre-registro v2,
        # cambio 2) U ≥ 0,5 → (0,5, no estricta)
        self.validez_minima = validez_minima
        self.validez_estricta = validez_estricta

    def es_valida(self, t: Theory) -> bool:
        return t.u > self.validez_minima if self.validez_estricta else t.u >= self.validez_minima

    # ---- utilidad usada para ordenar ----
    def u_orden(self, t: Theory) -> tuple[float, bool, Optional[float]]:
        """(U para ordenar, usó equidad, ê(t))."""
        e = None
        if self.alpha < 1.0 and self.registro_e is not None:
            e = e_paridad_errores(self.registro_e.lecturas(theory_key(t, self.base.q)),
                                  self.m_min)
        valor, usada = u_rol(t.u, e, self.alpha)
        return valor, usada, e

    def ordenar(self, teorias: list[Theory]) -> list[Theory]:
        """Fig. 4.21: U desc, P desc, K asc; desempate recencia desc, id asc."""
        return sorted(teorias, key=lambda t: (-self.u_orden(t)[0], -t.p, t.k,
                                              -t.created_at, t.id))

    @staticmethod
    def ordenar_alg47(teorias: list[Theory], u_de: Callable[[Theory], float]) -> list[Theory]:
        """Alg. 4.7 (p. 108): U desc y, a igual U, P/K desc; mismo desempate final."""
        return sorted(teorias, key=lambda t: (-u_de(t), -(t.p / t.k if t.k else 0.0),
                                              -t.created_at, t.id))

    def _fila(self, t: Theory, puesto: int) -> dict:
        u, usada, e = self.u_orden(t)
        return {"puesto": puesto, "id": t.id, "a": t.a, "sf": t.sf, "u_tarea": t.u,
                "u_orden": round(u, 6), "e": e, "p": t.p, "k": t.k}

    # ---- región 2 ----
    def planificar(self, si: dict, capa: str, accion_bio: str) -> DecisionPlan:
        celda = self.base.applicable(si)
        ordenadas = self.ordenar(celda)
        filas = [self._fila(t, i + 1) for i, t in enumerate(ordenadas)]
        equidad_usada = any(self.u_orden(t)[1] for t in ordenadas)
        desacuerdo = None
        if len(ordenadas) > 1:
            alg47 = self.ordenar_alg47(celda, lambda t: self.u_orden(t)[0])
            if alg47[0] is not ordenadas[0]:
                desacuerdo = {"fig_4_21": ordenadas[0].id, "alg_4_7": alg47[0].id}

        if ordenadas and self.es_valida(ordenadas[0]):
            t = ordenadas[0]
            return DecisionPlan(t.a, "celda", t, False, filas, False, desacuerdo,
                                self.alpha, equidad_usada)
        validez = bool(ordenadas)                      # había teoría pero no era plan válido

        if not celda and self.respaldo_similitud:
            parecidas = [t for t in self.base.theories
                         if self.es_valida(t) and self.similitud(si, t.si) >= self.delta]
            if parecidas:
                t = self.ordenar(parecidas)[0]
                filas_sim = [dict(self._fila(x, i + 1),
                                  similitud=round(self.similitud(si, x.si), 4))
                             for i, x in enumerate(self.ordenar(parecidas))]
                return DecisionPlan(t.a, "similitud", t, False, filas_sim, False, None,
                                    self.alpha, equidad_usada)

        if capa in self.capas_exploracion:
            probadas = {t.a for t in celda}
            no_probadas = [a for a in self.acciones if a not in probadas]
            if no_probadas:
                return DecisionPlan(no_probadas[0], "azar_no_probada", None, True, filas,
                                    validez, desacuerdo, self.alpha, equidad_usada)
        return DecisionPlan(accion_bio, "azar_bio", None, True, filas, validez, desacuerdo,
                            self.alpha, equidad_usada)
