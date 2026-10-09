"""
Motor del ciclo de vida del LLC dentro del agente — bloque E · E2.3 y E2.5 (G1–G4, G12).

Fuente: Ierache (2010), §4.2 (pp. 61–64): en cada ciclo percepción–acción el agente recorre
las siete regiones; los estados Born → Novice (newbie) → Trained → Mature se ganan
recorriendo las capas BIO → TBO → WIO, cada una en su escenario; la evolución (región 7)
sigue la Fig. 4.28 (§4.4.10, pp. 122–124).

Cada ciclo emite un evento de trail por región, con el número de región del LLC (G12):
  R1 situación inicial · R2 acción (planificador) · R3 situación final (la da el entorno,
  después de actuar) · R4 utilidad · R5 aprendizaje (registro de la Fig. 4.13) ·
  R6 estadísticas (§4.4.9) · R7 evolución (se evalúa al cierre de cada intervalo).

Regla de evolución (decisión P1 de Claude chat, adaptación declarada de la Fig. 4.28 y del
Anexo L-3; parámetros pre-registrados en configs/parada_tecnica.yaml):
  · CE_a = ciclos exitosos del agente en el intervalo (u_tarea > 0,75; p. 118);
  · CE_0 = ciclos exitosos del SAR neutro del mismo rol (solo operador BIO, sin teorías ni
    compartición) sobre los mismos casos: contrafáctico determinista del simulador;
  · %CEA = 100·(CE_a − CE_0)/max(CE_0, 1); condición %CEA ≥ %RCE;
  · %TN = 100·(teorías nuevas del intervalo)/n, solo si el agente recibió colaboración en
    la capa; condición %TN ≤ %RTN;
  · y el gate de Ω puntual (reputación ≥ τ; el certificado se informa, no se exige).
  Se evalúa al cierre de cada intervalo y se promueve apenas se cumple (P2); si se agotan
  los ciclos de la capa sin cumplirla, el agente queda en su estado y la corrida termina.

Genérico: el dominio entra por un objeto «rol» (RolLLC). No importa `instances/`.
"""
from __future__ import annotations
import warnings
from dataclasses import dataclass, field, replace
from typing import Any, Optional, Protocol

from moav_hr.core import fairness
from moav_hr.core.agent import MOACVAgent, TBOLayer
from moav_hr.core.audit.trail import AuditTrail
from moav_hr.core.equidad_roles import RegistroE
from moav_hr.core.estadisticas import EstadisticasLLC
from moav_hr.core.lifecycle import MaturityState, Region, capa_llc, next_state
from moav_hr.core.planificador import CAPAS_CON_EXPLORACION, PlanificadorLLC
from moav_hr.core.theory import serialize, theory_key

CAPAS = ("BIO", "TBO", "WIO")
M_TODAS = 10 ** 6
NOMBRE_ESTADO = {"born": "Born", "novato": "Novice", "trained": "Trained", "mature": "Mature"}


class RolLLC(Protocol):
    """Lo que el dominio aporta para que un rol recorra el ciclo."""
    nombre: str
    rol: str
    acciones: tuple[str, ...]

    def percibir(self, caso: Any) -> dict: ...                      # R1 (sin atributo protegido)
    def accion_bio(self, si: dict, caso: Any) -> str: ...           # operador BIO
    def observar(self, caso: Any, accion: str, capa: str) -> dict: ...   # R3 (entorno)
    def utilidad(self, si: dict, accion: str, sf: dict) -> float: ...     # R4: u_tarea
    def grupo(self, caso: Any) -> str: ...                           # plano de auditoría
    def fuente_sf(self, capa: str) -> str: ...
    def describir(self, caso: Any) -> dict: ...


class AgenteLLC(MOACVAgent):
    """Agente cuyo estado se GANA en el ciclo (G2): arranca en Born y solo cambia de estado
    por la regla de evolución. La capa es la que el estado transita en el LLC (G3)."""

    def __init__(self, nombre: str, rol: str):
        super().__init__(nombre, rol, tbo=TBOLayer(training_runs=0))
        self._estado = MaturityState.BORN

    @property
    def maturity(self) -> MaturityState:
        return self._estado

    @property
    def layer(self):
        return capa_llc(self._estado)

    def promover(self) -> tuple[MaturityState, MaturityState]:
        antes = self._estado
        self._estado = next_state(antes)
        return antes, self._estado


@dataclass
class ConfigCiclo:
    n_intervalo: int
    ciclos_por_capa: dict
    rce: float
    rtn: float
    umbral_exitoso: float = 0.75
    fin_en_mature: bool = True
    alpha: float = 1.0
    m_min: int = 5
    respaldo_similitud: bool = False
    delta: float = 0.7
    acciones_orden: tuple = ()
    attr: str = "origin_group"
    criterio: str = "demographic_parity"
    # pre-registro v2 (los defaults reproducen la v1)
    version: str = "v1"
    evaluacion: str = "por_intervalo"          # | "acumulada_en_la_capa"
    gate: str = "puntual"                      # | "evidencia_de_sesgo"
    utilidad_teoria: str = "u_tarea"           # | "accion"
    validez: str = "u_tarea_mayor_que_0"       # | "u_mayor_o_igual_0_5"
    tau_b: float = 0.075
    delta_omega: float = 0.05
    equidad_utilidad: str = "variante"         # E6 v2: | "celda" (ê(Si, A))

    @classmethod
    def desde_yaml(cls, cfg: dict, **cambios) -> "ConfigCiclo":
        cv, pl, ut, om = cfg["ciclo_de_vida"], cfg["planificador"], cfg["utilidad"], cfg["omega"]
        base = dict(n_intervalo=cv["n_intervalo"], ciclos_por_capa=dict(cv["ciclos_por_capa"]),
                    rce=cv["rce"], rtn=cv["rtn"], umbral_exitoso=cv["umbral_ciclo_exitoso"],
                    fin_en_mature=cv["fin_en_mature"], alpha=ut["alpha"],
                    m_min=ut["m_min_por_grupo"], respaldo_similitud=pl["respaldo_similitud"],
                    delta=pl["delta_similitud"], acciones_orden=tuple(pl["acciones_orden_fijo"]),
                    attr=om["atributo"], criterio=om["criterio"],
                    version=cfg.get("version_preregistro", "v1"),
                    evaluacion=cv.get("evaluacion", "por_intervalo"),
                    gate=om.get("gate_evolucion", "puntual"),
                    utilidad_teoria=pl.get("utilidad_teoria", "u_tarea"),
                    validez=pl.get("validez_plan", "u_tarea_mayor_que_0"),
                    tau_b=om.get("tau_b", 0.075), delta_omega=om.get("delta", 0.05))
        base.update(cambios)
        return cls(**base)


def evaluar_regla(ce_a: int, ce_0: int, nuevas: int, n: int, recibio_colaboracion: bool,
                  gate_omega: bool, rce: float, rtn: float) -> dict:
    """Regla de evolución de P1 (adaptación declarada de la Fig. 4.28) ∧ gate de Ω."""
    pct_cea = 100.0 * (ce_a - ce_0) / max(ce_0, 1)
    pct_tn = 100.0 * nuevas / n if recibio_colaboracion else None
    cumple_cea = pct_cea >= rce
    cumple_tn = True if pct_tn is None else pct_tn <= rtn
    return {"ce_a": ce_a, "ce_0": ce_0, "pct_cea": round(pct_cea, 2), "rce": rce,
            "cumple_cea": cumple_cea, "teorias_nuevas": nuevas,
            "pct_tn": None if pct_tn is None else round(pct_tn, 2), "rtn": rtn,
            "tn_aplica": recibio_colaboracion, "cumple_tn": cumple_tn,
            "gate_omega": gate_omega, "promueve": cumple_cea and cumple_tn and gate_omega}


@dataclass
class _Intervalo:
    ce_a: int = 0
    ce_0: int = 0
    nuevas: int = 0
    registros_fair: list = field(default_factory=list)


@dataclass
class _EstadoCapa:
    """Ciclos del agente en una capa: intervalo en curso y acumulado desde el inicio."""
    capa: str
    j: int = 0
    iv: _Intervalo = field(default_factory=_Intervalo)
    acum: _Intervalo = field(default_factory=_Intervalo)


class MotorLLC:
    def __init__(self, agente: AgenteLLC, rol: RolLLC, monitor, cfg: ConfigCiclo,
                 trail: Optional[AuditTrail] = None, registro_e: Optional[RegistroE] = None):
        self.agente, self.rol, self.monitor, self.cfg = agente, rol, monitor, cfg
        # `is None`, no `or`: un AuditTrail vacío es falso (len 0) y el equipo comparte uno
        self.trail = trail if trail is not None else AuditTrail("TRC-LLC")
        self.registro_e = registro_e if registro_e is not None else RegistroE()
        self.registro_celda = RegistroE()             # E(Si, A) de la E6 v2 (plano de auditoría)
        self.planificador = PlanificadorLLC(
            agente.theories, cfg.acciones_orden or rol.acciones,
            respaldo_similitud=cfg.respaldo_similitud, delta=cfg.delta, alpha=cfg.alpha,
            registro_e=self.registro_e, m_min=cfg.m_min,
            capas_exploracion=getattr(rol, "capas_exploracion", CAPAS_CON_EXPLORACION),
            equidad=cfg.equidad_utilidad, registro_celda=self.registro_celda,
            **self.parametros_validez(cfg))
        self.stats = EstadisticasLLC(cfg.umbral_exitoso)
        self.ciclo = 0
        self.ciclos: list[dict] = []
        self.evaluaciones: list[dict] = []
        self.recibio_colaboracion: dict[str, bool] = {c: False for c in CAPAS}
        self._ec: Optional[_EstadoCapa] = None        # capa en curso en el modo equipo (paso)

    @staticmethod
    def parametros_validez(cfg: ConfigCiclo) -> dict:
        if cfg.validez == "u_mayor_o_igual_0_5":
            return {"validez_minima": 0.5, "validez_estricta": False}
        return {"validez_minima": 0.0, "validez_estricta": True}

    def es_acierto(self, t) -> bool:
        """La Sf de la variante hace correcta su acción (para U basada en la acción)."""
        return self.rol.utilidad(t.si, t.a, t.sf) > self.cfg.umbral_exitoso

    def recalcular_u(self) -> None:
        """Con U basada en la acción, recalcula U(Si, A) en toda la base (tras compartir)."""
        if self.cfg.utilidad_teoria == "accion":
            self.agente.theories.recalcular_u_accion_todas(self.es_acierto)

    def _evento(self, region: Region, nombre_evento: str, capa: str, estado: str, **detalle):
        self.trail.record(self.agente.name, capa, nombre_evento, region=int(region),
                          ciclo=self.ciclo, capa=capa, estado=estado, **detalle)

    # ---- un ciclo percepción–acción: regiones 1 a 6 (la 7 la decide correr_capa) ----
    def ciclo_llc(self, caso: Any, capa: str, ciclo_capa: int) -> dict:
        self.ciclo += 1
        estado = NOMBRE_ESTADO[self.agente.maturity.label]
        si = self.rol.percibir(caso)                                              # R1
        self._evento(Region.SITUATION_INIT, "R1_situacion_inicial", capa, estado,
                     caso=self.rol.describir(caso), si=serialize(si))
        bio = self.rol.accion_bio(si, caso)                                       # R2
        plan = self.planificador.planificar(si, capa, bio)
        if getattr(self.rol, "accion_por_regla", False):
            # DE-6: decide la regla (operador BIO); las candidatas quedan en la traza. También
            # el SAR neutro de L-3 (E5), que actúa solo con su operador BIO.
            plan = replace(plan, accion=bio, teoria=None, es_azar=False,
                           motivo=getattr(self.rol, "motivo_regla", "regla_certificada"))
        self._evento(Region.ACTION, "R2_accion", capa, estado, accion=plan.accion,
                     motivo=plan.motivo, es_azar=plan.es_azar,
                     teoria_plan=None if plan.teoria is None else plan.teoria.id,
                     candidatas=[f"T{c['id']} {c['a']} Sf={serialize(c['sf'])} "
                                 f"(U={c['u_orden']}, P={c['p']}, K={c['k']})"
                                 for c in plan.candidatas],
                     validez_aplicada=plan.validez_aplicada,
                     desacuerdo_alg47=plan.desacuerdo_alg47, accion_bio=bio)
        sf = self.rol.observar(caso, plan.accion, capa)                           # R3
        self._evento(Region.SITUATION_FINAL, "R3_situacion_final", capa, estado,
                     sf=serialize(sf), fuente=self.rol.fuente_sf(capa))
        u = self.rol.utilidad(si, plan.accion, sf)                                # R4
        self._evento(Region.UTILITY, "R4_utilidad", capa, estado, u_tarea=u,
                     alpha=self.cfg.alpha)
        t, tipo = self.agente.learn_llc(si, plan.accion, sf, u)                   # R5
        if self.cfg.utilidad_teoria == "accion":       # v2: U(Si, A), igual en la celda
            self.agente.theories.recalcular_u_accion(si, plan.accion, self.es_acierto)
        self._evento(Region.LEARNING, "R5_aprendizaje", capa, estado, teoria=t.id,
                     registro=tipo, p=t.p, k=t.k, u=t.u, u_tarea_del_ciclo=u,
                     utilidad_teoria=self.cfg.utilidad_teoria,
                     clave=serialize(list(theory_key(t, self.agente.theories.q))))
        grupo = self.rol.grupo(caso)                                   # plano de auditoría
        acierto = u > self.cfg.umbral_exitoso
        if plan.teoria is not None:                                    # E(t): t fue el plan
            self.registro_e.registrar(theory_key(plan.teoria, self.agente.theories.q),
                                      grupo, acierto)
        self.registro_celda.registrar(self.planificador.clave_celda(si, plan.accion), grupo,
                                      acierto)                         # E(Si, A), E6 v2
        plan_valido = plan.motivo in ("celda", "similitud")
        plan_exitoso = plan_valido and plan.teoria is not None and sf == plan.teoria.sf
        exitoso = self.stats.registrar_ciclo(serialize(si), tipo, u, plan.es_azar,   # R6
                                             plan_valido, plan_exitoso)
        foto = self.stats.instantanea(self.agente.theories)
        self._evento(Region.STATISTICS, "R6_estadisticas", capa, estado, **foto)
        # CE_0: el SAR neutro con el operador BIO sobre el mismo caso. Si la Sf no depende de
        # la acción (Matcher, Auditor), es la misma Sf; si depende (Parser, Explainer), el rol
        # da la Sf contrafáctica del operador BIO, sin efectos sobre el caso.
        contrafactico = getattr(self.rol, "sf_contrafactica", None)
        sf_bio = sf if contrafactico is None or bio == plan.accion else \
            contrafactico(caso, bio, capa)
        acierto_bio = self.rol.utilidad(si, bio, sf_bio) > self.cfg.umbral_exitoso
        reg = {"ciclo": self.ciclo, "capa": capa, "ciclo_capa": ciclo_capa, "estado": estado,
               "caso": self.rol.describir(caso), "si": si, "accion": plan.accion,
               "motivo": plan.motivo, "es_azar": plan.es_azar,
               "teoria_plan": None if plan.teoria is None else plan.teoria.id,
               "candidatas": plan.candidatas, "validez_aplicada": plan.validez_aplicada,
               "desacuerdo_alg47": plan.desacuerdo_alg47, "accion_bio": bio,
               "acierto_bio": acierto_bio, "sf": sf, "fuente_sf": self.rol.fuente_sf(capa),
               "u_tarea": u, "teoria_registrada": t.id, "registro": tipo,
               "p": t.p, "k": t.k, "u": t.u, "exitoso": exitoso, "grupo": grupo,
               "estadisticas": foto}
        if self.cfg.alpha < 1.0:            # DE-5 (E6): uso de ê(t) y elección con α = 1
            reg.update(equidad_usada=plan.equidad_usada, plan_alpha_1=plan.alpha_1)
            if self.cfg.equidad_utilidad == "celda":
                reg["ajuste_equidad"] = plan.ajuste_equidad
        self.ciclos.append(reg)
        return reg

    # ---- región 7 al cierre del intervalo ----
    def _evaluar(self, capa: str, ciclo_capa: int, iv: _Intervalo, acum: _Intervalo,
                 estado: str) -> dict:
        # fair(W) de la ventana (n ciclos): alimenta la reputación r y can_donate (A9)
        fair_w = fairness.fair_window(iv.registros_fair, self.cfg.attr, self.cfg.criterio)
        self.agente.record_window_fairness(fair_w)
        gate_puntual = bool(self.monitor.gate_evolution(self.agente))
        with warnings.catch_warnings(record=True) as avisos:
            warnings.simplefilter("always")
            cert = bool(self.monitor.gate_evolution(self.agente, certified=True, m=M_TODAS))
        evidencia = None
        if self.cfg.gate == "evidencia_de_sesgo":       # v2: decide la cota, no la reputación
            n_cierres = self.cfg.ciclos_por_capa[capa] // self.cfg.n_intervalo
            evidencia = self.monitor.gate_evidencia_sesgo(acum.registros_fair, n_cierres,
                                                          self.cfg.delta_omega)
            gate = evidencia["aprueba"]
        else:
            gate = gate_puntual
        if self.cfg.evaluacion == "acumulada_en_la_capa":   # v2: desde el inicio de la capa
            base, n_den = acum, ciclo_capa
        else:
            base, n_den = iv, self.cfg.n_intervalo
        regla = evaluar_regla(base.ce_a, base.ce_0, base.nuevas, n_den,
                              self.recibio_colaboracion[capa], gate, self.cfg.rce,
                              self.cfg.rtn)
        ev = {"ciclo": self.ciclo, "capa": capa, "ciclo_capa": ciclo_capa,
              "estado_antes": estado, "evaluacion": self.cfg.evaluacion,
              "gate_tipo": self.cfg.gate, "fair_w": fair_w,
              "reputacion": self.agente.reputation(), "tau": self.monitor.tau,
              "gate_puntual_informado": gate_puntual, "gate_certificado": cert,
              "aviso_certificado": str(avisos[0].message) if avisos else None,
              "evidencia_sesgo": evidencia, **regla}
        if regla["promueve"]:
            _, despues = self.agente.promover()
            ev["estado_despues"] = NOMBRE_ESTADO[despues.label]
        else:
            ev["estado_despues"] = estado
        self.evaluaciones.append(ev)
        return ev

    def _registros_equidad(self, caso: Any, reg: dict) -> list[dict]:
        """Registros del plano de auditoría para Ω. Sin `resultado_equidad` en el rol (el
        Matcher), la decisión del ciclo, como en v1 y v2. Con él (E4), `decision` = ADVANCE
        codifica el resultado favorable del rol (perfil completo, explicación completa,
        ventana derivada) y lo demás, REJECT."""
        f = getattr(self.rol, "resultado_equidad", None)
        if f is None:
            return [{self.cfg.attr: reg["grupo"], "decision": reg["accion"]}]
        return [{self.cfg.attr: g, "decision": "ADVANCE" if favorable else "REJECT"}
                for g, favorable in f(caso, reg)]

    def _lecturas_equidad(self, caso: Any, reg: dict) -> list[tuple[str, bool]]:
        """(grupo, resultado favorable) del ciclo, para la ABox del equipo (e_rol)."""
        return [(str(r[self.cfg.attr]), r["decision"] in fairness.POSITIVE)
                for r in self._registros_equidad(caso, reg)]

    def _paso_en_capa(self, caso: Any, ec: "_EstadoCapa") -> tuple[dict, Optional[dict]]:
        """Un ciclo en la capa `ec.capa` y, al cierre del intervalo, la región 7."""
        ec.j += 1
        j = ec.j
        reg = self.ciclo_llc(caso, ec.capa, j)
        for x in (ec.iv, ec.acum):
            x.ce_a += reg["exitoso"]
            x.ce_0 += reg["acierto_bio"]
            x.nuevas += reg["registro"] in ("nueva", "similar")
            x.registros_fair.extend(self._registros_equidad(caso, reg))
        if j % self.cfg.n_intervalo == 0:
            ev = self._evaluar(ec.capa, j, ec.iv, ec.acum, reg["estado"])
            self._evento(Region.EVOLUTION, "R7_evolucion", ec.capa, reg["estado"],
                         evaluada=True, **{k: v for k, v in ev.items()
                                           if k not in ("ciclo", "capa")})
            ec.iv = _Intervalo()
            return reg, ev
        self._evento(Region.EVOLUTION, "R7_evolucion", ec.capa, reg["estado"],
                     evaluada=False, proxima_evaluacion=(
                         (j // self.cfg.n_intervalo) + 1) * self.cfg.n_intervalo)
        return reg, None

    def correr_capa(self, capa: str, casos: list) -> dict:
        n_ciclos = self.cfg.ciclos_por_capa[capa]
        if len(casos) < n_ciclos:
            raise ValueError(f"la capa {capa} necesita {n_ciclos} casos")
        ec = _EstadoCapa(capa)                         # ventana del intervalo y acumulado
        for j in range(1, n_ciclos + 1):
            _, ev = self._paso_en_capa(casos[j - 1], ec)
            if ev is not None and ev["promueve"]:
                return {"capa": capa, "promovido": True, "ciclos": j}
        return {"capa": capa, "promovido": False, "ciclos": n_ciclos}

    def paso(self, caso: Any) -> dict:
        """Un ciclo del rol dentro de un equipo (E4): la capa es la del estado ganado del
        agente y los contadores, intervalos y región 7 son propios del rol. Con la capa
        agotada sin promoción, o en Mature, el rol sigue actuando y aprendiendo (regiones
        1 a 6) sin evaluar la región 7 (pre-registro E4). Un rol con `evoluciona = False`
        (E5: el Bias Auditor, rol supervisor) no aplica la región 7."""
        capa = self.agente.layer.value
        if self._ec is None or self._ec.capa != capa:
            self._ec = _EstadoCapa(capa)
        ec = self._ec
        final = self.agente.maturity == MaturityState.MATURE
        evoluciona = getattr(self.rol, "evoluciona", True)
        if not evoluciona or final or ec.j >= self.cfg.ciclos_por_capa[capa]:
            ec.j += 1
            reg = self.ciclo_llc(caso, capa, ec.j)
            motivo = (getattr(self.rol, "motivo_sin_r7", "el rol no evoluciona")
                      if not evoluciona else "estado final (Mature)" if final
                      else "capa agotada sin promoción")
            self._evento(Region.EVOLUTION, "R7_evolucion", capa, reg["estado"],
                         evaluada=False, sin_r7=motivo)
            reg.update(evolucion=None, sin_r7=motivo,
                       equidad=self._lecturas_equidad(caso, reg))
            return reg
        reg, ev = self._paso_en_capa(caso, ec)
        reg.update(evolucion=ev, sin_r7=None, equidad=self._lecturas_equidad(caso, reg))
        return reg

    def correr(self, escenarios: dict) -> dict:
        """Recorre BIO → TBO → WIO desde el estado actual del agente."""
        capas = []
        for capa in CAPAS:
            if self.agente.layer.value != capa:
                continue
            if self.agente.maturity == MaturityState.MATURE:
                break
            res = self.correr_capa(capa, escenarios[capa])
            capas.append(res)
            if not res["promovido"]:
                break
            if self.agente.maturity == MaturityState.MATURE and self.cfg.fin_en_mature:
                break
        return {"capas": capas, "estado_final": NOMBRE_ESTADO[self.agente.maturity.label],
                "ciclos": self.ciclo, "estadisticas": self.stats.instantanea(
                    self.agente.theories)}
