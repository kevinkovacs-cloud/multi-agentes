"""
Equipo DAG en el modo LLC — instancia HR (bloque E · E4, punto 4; base de E5).

Cada rol del equipo es un AgenteLLC con su propio MotorLLC: su estado se gana con su propio
ciclo de vida (contadores, intervalos y región 7 propios; pre-registro E4). El DAG de cada
ventana de casos es un StateGraph de LangGraph (`core/grafo.py`, DE-10):

    Parser → Semantic Matcher → Bias Auditor → Orchestrator → Explainer

  · Parser, Matcher y Explainer hacen un ciclo del LLC por caso; el Bias Auditor, uno por
    ventana (DE-6), con la acción decidida por la regla certificada.
  · El Orchestrator no tiene teorías (DE-7): registra la decisión final de cada caso
    (ESCALATE_HUMAN si la ventana se derivó; si no, la del Matcher) y el escalamiento.
  · El Explainer va al final porque explica la decisión final y el dictamen de la ventana.

Cada rol transita la capa de su estado ganado; el escenario del flujo solo fija qué casos
llegan (adaptación declarada en el pre-registro E4).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional

from moav_hr.core.audit.events import EventType
from moav_hr.core.audit.trail import AuditTrail
from moav_hr.core.ciclo_llc import NOMBRE_ESTADO, AgenteLLC, ConfigCiclo, MotorLLC
from moav_hr.core.grafo import construir_grafo
from moav_hr.core.monitor import FairnessMonitor
from moav_hr.instances.hr import entorno
from moav_hr.instances.hr.roles_llc import (RolAuditorLLC, RolExplainerLLC, RolMatcherEquipo,
                                            RolNeutro, RolParserLLC)

ROLES = ("parser", "matcher", "bias_auditor", "explainer")
NOMBRE_ROL = {"parser": "Parser", "matcher": "SemanticMatcher", "bias_auditor": "BiasAuditor",
              "explainer": "Explainer"}


@dataclass
class CasoEquipo:
    """Un caso que recorre el DAG; cada nodo completa lo suyo."""
    caso: entorno.Caso
    escenario: str
    ventana: str
    trace_id: str
    documento: Any
    plantilla: int
    defecto: bool
    perfil: Optional[dict] = None
    validacion_perfil: Optional[dict] = None
    si_parser: Optional[dict] = None
    si_matcher: Optional[dict] = None
    si_explainer: Optional[dict] = None
    si_explainer_entorno: Optional[dict] = None      # con los motivos del caso (regla 10)
    decision_matcher: Optional[str] = None
    motivo_matcher: Optional[str] = None
    teoria_matcher: Optional[dict] = None
    dictamen: Optional[dict] = None
    decision_final: Optional[str] = None
    explicacion: Optional[dict] = None
    verificacion_explicacion: Optional[dict] = None
    ciclos: dict = field(default_factory=dict)        # rol → registro del ciclo del rol

    @property
    def grupo(self) -> str:
        return self.caso.grupo

    @property
    def numero(self) -> int:
        return self.caso.indice + 1

    def hechos(self) -> dict:
        """Lo que el Explainer sabe del caso (sin el atributo protegido, DE-4)."""
        return {"resultado": self.decision_final, "ventana": self.ventana,
                "trace_id": self.trace_id, "si_matcher": self.si_matcher,
                "teoria": self.teoria_matcher, "dictamen": self.dictamen}


@dataclass
class VentanaEquipo:
    id: str
    escenario: str
    casos: list
    medida: Optional[dict] = None
    ciclo_auditor: Optional[dict] = None

    @property
    def decisiones(self) -> list[tuple[str, str]]:
        return [(ce.grupo, ce.decision_matcher) for ce in self.casos]


class _Nodo:
    """Nodo del DAG: misma interfaz que un agente del orquestador (`name`, `run`)."""

    def __init__(self, name: str, f):
        self.name, self._f = name, f

    def run(self, state: dict) -> dict:
        self._f(state)
        return state


def seccion_equipo(cfg: dict, seccion: str, semillas: Optional[dict] = None) -> dict:
    """Sección del equipo en la config. Una sección con `base` hereda la base y la pisa con
    lo suyo (E5 hereda de E4). `semillas` = {casos, documentos, destinatario} del equipo."""
    eq = dict(cfg[seccion])
    if "base" in eq:                                   # la base puede heredar de otra (E6 → E5 → E4)
        eq = {**seccion_equipo(cfg, eq["base"]), **eq}
    if semillas is not None:
        eq.update(semilla_casos=semillas["casos"], semilla_documentos=semillas["documentos"],
                  semilla_destinatario=semillas["destinatario"])
    return eq


class EquipoLLC:
    def __init__(self, nombre: str, cfg: dict, seccion: str = "equipo_e4",
                 semillas: Optional[dict] = None, neutro: bool = False,
                 alpha: Optional[float] = None):
        self.nombre, self.cfg, self.neutro = nombre, cfg, neutro
        eq, om = seccion_equipo(cfg, seccion, semillas), cfg["omega"]
        if alpha is not None:                              # E6: α = 1 y α = 0,5 lado a lado
            eq["alpha"] = alpha
        self.eq = eq
        eps = cfg["entorno"]["ruido_wio_epsilon"]
        self.trail = AuditTrail(f"TRC-{nombre}")
        self.monitor = FairnessMonitor(tau=om["tau"], attr=om["atributo"],
                                       criterion=om["criterio"],
                                       disparity_threshold=om.get("tau_b", 0.075))
        roles = {"parser": RolParserLLC(),
                 "matcher": RolMatcherEquipo(eps, eq["semilla_casos"]),
                 "bias_auditor": RolAuditorLLC(eps, eq["semilla_casos"], om["tau_b"],
                                               om["delta"],
                                               evoluciona=eq.get("auditor_evoluciona", True)),
                 "explainer": RolExplainerLLC(eq["semilla_destinatario"], con_motivos=(
                     "motivos" in eq.get("si_explainer", ["tipo", "destinatario", "motivos"])))}
        for r in eq.get("explora_en_wio", []):           # E5, decisión 3
            roles[r].capas_exploracion = ("BIO", "TBO", "WIO")
        if neutro:                                         # SAR neutro de L-3 (E5)
            roles = {r: RolNeutro(x) for r, x in roles.items()}
        self.roles = roles
        self.agentes = {r: AgenteLLC(f"{nombre}-{NOMBRE_ROL[r]}", r) for r in ROLES}
        self.motores = {}
        for r in ROLES:
            c = ConfigCiclo.desde_yaml(cfg, alpha=eq["alpha"], acciones_orden=tuple(
                eq["roles"][r]["acciones_orden_fijo"]))
            self.motores[r] = MotorLLC(self.agentes[r], roles[r], self.monitor, c,
                                       trail=self.trail)
        self.ventanas: list[VentanaEquipo] = []
        self.casos: list[CasoEquipo] = []
        self.linea_de_tiempo: list[dict] = []          # estados de los roles tras cada ventana
        self.grafo = construir_grafo([
            _Nodo("Parser", self._nodo_parser), _Nodo("SemanticMatcher", self._nodo_matcher),
            _Nodo("BiasAuditor", self._nodo_auditor), _Nodo("Orchestrator", self._nodo_orq),
            _Nodo("Explainer", self._nodo_explainer)])

    # ---- nodos del DAG ----
    def _ciclo(self, rol: str, ce) -> dict:
        reg = self.motores[rol].paso(ce)
        ce.ciclos[rol] = reg
        return reg

    def _nodo_parser(self, state: dict) -> None:
        for ce in state["ventana"].casos:
            self._ciclo("parser", ce)

    def _nodo_matcher(self, state: dict) -> None:
        for ce in state["ventana"].casos:
            reg = self._ciclo("matcher", ce)
            ce.decision_matcher, ce.motivo_matcher = reg["accion"], reg["motivo"]
            fila = next((c for c in reg["candidatas"] if c["id"] == reg["teoria_plan"]), None)
            ce.teoria_matcher = None if fila is None else {   # P, K y U al momento de decidir
                "id": fila["id"], "p": fila["p"], "k": fila["k"], "u": fila["u_tarea"]}

    def _nodo_auditor(self, state: dict) -> None:
        v = state["ventana"]
        reg = self.motores["bias_auditor"].paso(v)
        v.ciclo_auditor = reg
        dictamen = {**(v.medida or {}), "tau_b": self.cfg["omega"]["tau_b"],
                    "accion": reg["accion"]}
        for ce in v.casos:
            ce.dictamen = dictamen
            ce.ciclos["bias_auditor"] = reg

    def _nodo_orq(self, state: dict) -> None:
        v = state["ventana"]
        derivada = v.ciclo_auditor["accion"] == "DERIVAR"
        for ce in v.casos:
            ce.decision_final = "ESCALATE_HUMAN" if derivada else ce.decision_matcher
            ev = (EventType.ESCALAMIENTO.value if derivada else EventType.DECISION.value)
            self.trail.record("Orchestrator", "BIO", "final_decision", event_type=ev,
                              region=7, decision=ce.decision_final, caso=ce.caso.candidato.id,
                              ventana=v.id, sin_teorias="DE-7")

    def _nodo_explainer(self, state: dict) -> None:
        for ce in state["ventana"].casos:
            self._ciclo("explainer", ce)

    # ---- flujo ----
    def _ventanas(self, escenario: str, casos: list) -> list[VentanaEquipo]:
        w = self.eq["ventana"]
        ventanas = []
        for k in range(0, len(casos), w):
            vid = f"{escenario}-W{k // w + 1:02d}"
            lote = []
            for caso in casos[k:k + w]:
                doc, idx, defecto = entorno.generar_documento(caso, self.eq["semilla_documentos"])
                lote.append(CasoEquipo(caso, escenario, vid,
                                       f"TRC-{self.nombre}-{escenario}-{caso.indice + 1:03d}",
                                       doc, idx, defecto))
            ventanas.append(VentanaEquipo(vid, escenario, lote))
        return ventanas

    def procesar_ventana(self, v: VentanaEquipo) -> VentanaEquipo:
        self.grafo.invoke({"estado": {"trace_id": f"TRC-{self.nombre}-{v.id}",
                                      "trail": self.trail, "ventana": v}})
        self.ventanas.append(v)
        self.casos.extend(v.casos)
        self.linea_de_tiempo.append({"ventana": v.id, "casos": len(self.casos),
                                     "estados": self.estados()})
        return v

    def ventanas_del_flujo(self, escenarios: Optional[dict] = None) -> list[VentanaEquipo]:
        """Las ventanas del flujo de casos del equipo, sin procesar (para correr en paralelo)."""
        cv = self.cfg["ciclo_de_vida"]
        if escenarios is None:                  # E6: `flujo_casos` alarga el flujo (600 casos)
            n = {c: self.eq.get("flujo_casos", {}).get(c, cv["ciclos_por_capa"][c])
                 for c in self.eq["flujo"]}
            escenarios = {c: entorno.generar_escenario(c, n[c], self.eq["semilla_casos"])
                          for c in self.eq["flujo"]}
        return [v for esc in self.eq["flujo"] for v in self._ventanas(esc, escenarios[esc])]

    def correr(self, escenarios: Optional[dict] = None) -> dict:
        for v in self.ventanas_del_flujo(escenarios):
            self.procesar_ventana(v)
        return self.resumen()

    def estados(self) -> dict:
        return {r: NOMBRE_ESTADO[self.agentes[r].maturity.label] for r in ROLES}

    def resumen(self) -> dict:
        out = {}
        for r in ROLES:
            m = self.motores[r]
            out[r] = {"agente": self.agentes[r].name, "estado": self.estados()[r],
                      "ciclos": m.ciclo, "teorias": len(self.agentes[r].theories),
                      "promociones": [{"ciclo": e["ciclo"], "de": e["estado_antes"],
                                       "a": e["estado_despues"]}
                                      for e in m.evaluaciones if e["promueve"]],
                      "evaluaciones": len(m.evaluaciones)}
        return {"equipo": self.nombre, "casos": len(self.casos), "ventanas": len(self.ventanas),
                "roles": out, "orchestrator": "sin teorías (DE-7)"}
