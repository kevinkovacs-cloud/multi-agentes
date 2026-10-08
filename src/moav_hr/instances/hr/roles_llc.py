"""
Roles del equipo DAG en el modo LLC — instancia HR (bloque E; sección 6 del handoff).

E2 implementa el rol decisor, el Semantic Matcher (puntos 1 y 2b del pedido):
  · Si (R1): `build_si` del perfil normalizado (skills clave, banda de experiencia,
    educación, antigüedad mínima), sin atributos protegidos (DE-4).
  · A (R2): ADVANCE o REJECT. Operador BIO: la regla del diseñador de `entorno.py`.
  · Sf (R3): {"calificado": sí/no}; en BIO y TBO la etiqueta del escenario de
    entrenamiento, en WIO la revisión humana simulada. Llega después de actuar.
  · u_tarea (R4): 1 si la acción fue la correcta para el resultado observado; 0 si no.
E4 agrega los demás roles del equipo (reglas 7 a 10 de `entorno.py`; pre-registro E4):
  · RolParserLLC: Si = plantilla del documento; A = estrategia de extracción; Sf =
    completitud y fuga del perfil, validadas por el shape SHACL del perfil.
  · RolMatcherEquipo: el Matcher de E2, pero percibe el perfil EXTRAÍDO por el Parser.
  · RolAuditorLLC (DE-6): un ciclo por ventana; la acción la decide la regla certificada
    (`accion_por_regla`); Sf = resultado de la revisión de la ventana.
  · RolExplainerLLC: Si = tipo, destinatario y motivos; A = estrategia de explicación; Sf =
    completitud verificada contra el grafo RDF del caso.
Cada rol del equipo declara `resultado_equidad`: el resultado favorable del rol por grupo,
para el gate de Ω y e_rol (plano de auditoría; nunca en Si, A ni los prompts, DE-4).
El Orchestrator no tiene teorías (DE-7).
"""
from __future__ import annotations

from moav_hr.instances.hr import entorno
from moav_hr.instances.hr.estrategias_llc import explicar, extraer
from moav_hr.instances.hr.parser_agent import build_si, normalize_profile


class RolMatcherLLC:
    nombre = "SemanticMatcher"
    rol = "matcher"
    acciones = entorno.ACCIONES

    def __init__(self, epsilon_wio: float, semilla: int):
        self.epsilon_wio = epsilon_wio
        self.semilla = semilla

    def percibir(self, caso: entorno.Caso) -> dict:
        return build_si(normalize_profile(caso.candidato))

    def accion_bio(self, si: dict, caso: entorno.Caso) -> str:
        return entorno.operador_bio_matcher(si)

    def observar(self, caso: entorno.Caso, accion: str, capa: str) -> dict:
        return entorno.observar(caso, capa, self.epsilon_wio, self.semilla)

    def utilidad(self, si: dict, accion: str, sf: dict) -> float:
        return 1.0 if (accion == "ADVANCE") == bool(sf["calificado"]) else 0.0

    def grupo(self, caso: entorno.Caso) -> str:
        return caso.grupo

    @staticmethod
    def fuente_sf(capa: str) -> str:
        return ("etiqueta del escenario de entrenamiento" if capa in ("BIO", "TBO")
                else "revisión humana simulada (human_sim, modo noisy)")

    @staticmethod
    def describir(caso: entorno.Caso) -> dict:
        c = caso.candidato
        return {"id": c.id, "nombre": c.name, "skills": list(c.skills), "exp": c.exp,
                "edu": c.edu}


# ------------------------------ E4: roles del equipo ------------------------------
class RolParserLLC:
    nombre = "Parser"
    rol = "parser"
    acciones = entorno.ESTRATEGIAS_PARSER

    def percibir(self, ce) -> dict:
        ce.si_parser = entorno.percibir_documento(ce.documento)
        return ce.si_parser

    def accion_bio(self, si: dict, ce) -> str:
        return entorno.OPERADOR_BIO_PARSER

    def observar(self, ce, accion: str, capa: str) -> dict:
        ce.perfil = extraer(accion, ce.documento)              # se ejecuta la estrategia
        v = entorno.validar_perfil(ce.perfil)                  # y el entorno la valida
        ce.validacion_perfil = v
        return {"completitud": v["completitud"], "fuga": v["fuga"]}

    def sf_contrafactica(self, ce, accion: str, capa: str) -> dict:
        """Sf que habría dado `accion` sobre el mismo documento (para CE_0), sin efectos."""
        v = entorno.validar_perfil(extraer(accion, ce.documento))
        return {"completitud": v["completitud"], "fuga": v["fuga"]}

    def utilidad(self, si: dict, accion: str, sf: dict) -> float:
        return entorno.u_parser(sf)

    def grupo(self, ce) -> str:
        return ce.grupo

    def resultado_equidad(self, ce, reg: dict) -> list[tuple[str, bool]]:
        return [(ce.grupo, reg["sf"]["completitud"] == "completo")]

    @staticmethod
    def fuente_sf(capa: str) -> str:
        return "validación SHACL del perfil extraído (PerfilShape)"

    @staticmethod
    def describir(ce) -> dict:
        return {"id": ce.caso.candidato.id, "nombre": ce.caso.candidato.name,
                "plantilla": ce.plantilla, "defecto": ce.defecto}


class RolMatcherEquipo(RolMatcherLLC):
    """El Matcher de E2 dentro del equipo: percibe el perfil extraído (regla 8)."""

    def percibir(self, ce) -> dict:
        ce.si_matcher = build_si(entorno.perfil_para_matcher(ce.perfil or {}))
        return ce.si_matcher

    def accion_bio(self, si: dict, ce) -> str:
        return entorno.operador_bio_matcher(si)

    def observar(self, ce, accion: str, capa: str) -> dict:
        return entorno.observar(ce.caso, capa, self.epsilon_wio, self.semilla)

    def grupo(self, ce) -> str:
        return ce.grupo

    def resultado_equidad(self, ce, reg: dict) -> list[tuple[str, bool]]:
        return [(ce.grupo, reg["accion"] == "ADVANCE")]

    @staticmethod
    def describir(ce) -> dict:
        return RolMatcherLLC.describir(ce.caso)


class RolAuditorLLC:
    nombre = "BiasAuditor"
    rol = "bias_auditor"
    acciones = entorno.ACCIONES_AUDITOR
    accion_por_regla = True                                     # DE-6

    def __init__(self, epsilon_wio: float, semilla: int, tau_b: float, delta: float):
        self.epsilon_wio, self.semilla = epsilon_wio, semilla
        self.tau_b, self.delta = tau_b, delta

    def percibir(self, v) -> dict:
        v.medida = entorno.medida_ventana(v.decisiones, self.delta)
        return entorno.situacion_ventana(v.decisiones, self.tau_b, self.delta)

    def accion_bio(self, si: dict, v) -> str:
        return entorno.regla_certificada(si)

    def observar(self, v, accion: str, capa: str) -> dict:
        return entorno.revisar_ventana([ce.caso for ce in v.casos],
                                       [d for _, d in v.decisiones], capa, self.epsilon_wio,
                                       self.semilla, self.tau_b, self.delta)

    def utilidad(self, si: dict, accion: str, sf: dict) -> float:
        return entorno.u_auditor(accion, sf)

    def grupo(self, v) -> str:
        return "ventana"                                        # la ventana tiene los dos grupos

    def resultado_equidad(self, v, reg: dict) -> list[tuple[str, bool]]:
        return [(ce.grupo, reg["accion"] == "DERIVAR") for ce in v.casos]

    @staticmethod
    def fuente_sf(capa: str) -> str:
        return ("revisión de la ventana con la etiqueta del escenario" if capa in ("BIO", "TBO")
                else "revisión de la ventana con human_sim (noisy)")

    @staticmethod
    def describir(v) -> dict:
        return {"ventana": v.id, "casos": [ce.caso.candidato.id for ce in v.casos],
                **(v.medida or {})}


class RolExplainerLLC:
    nombre = "Explainer"
    rol = "explainer"
    acciones = entorno.ESTRATEGIAS_EXPLAINER

    def __init__(self, semilla_destinatario: int):
        self.semilla = semilla_destinatario

    def percibir(self, ce) -> dict:
        ce.si_explainer = {"tipo": entorno.TIPOS_DECISION[ce.decision_final],
                           "destinatario": entorno.destinatario(ce.caso, self.semilla),
                           "motivos": "varios" if ce.motivo_matcher in ("celda", "similitud")
                           else "uno"}
        return ce.si_explainer

    def accion_bio(self, si: dict, ce) -> str:
        return entorno.OPERADOR_BIO_EXPLAINER

    def observar(self, ce, accion: str, capa: str) -> dict:
        hechos = ce.hechos()
        ce.explicacion = explicar(accion, hechos)
        v = entorno.verificar_explicacion(ce.explicacion, ce.si_explainer,
                                          entorno.grafo_hechos_caso(hechos))
        ce.verificacion_explicacion = v
        return {"completa": v["completa"]}

    def sf_contrafactica(self, ce, accion: str, capa: str) -> dict:
        """Sf que habría dado `accion` con los mismos hechos (para CE_0), sin efectos."""
        hechos = ce.hechos()
        v = entorno.verificar_explicacion(explicar(accion, hechos), ce.si_explainer,
                                          entorno.grafo_hechos_caso(hechos))
        return {"completa": v["completa"]}

    def utilidad(self, si: dict, accion: str, sf: dict) -> float:
        return 1.0 if sf["completa"] else 0.0

    def grupo(self, ce) -> str:
        return ce.grupo

    def resultado_equidad(self, ce, reg: dict) -> list[tuple[str, bool]]:
        return [(ce.grupo, bool(reg["sf"]["completa"]))]

    @staticmethod
    def fuente_sf(capa: str) -> str:
        return "verificación SPARQL contra el grafo RDF del caso"

    @staticmethod
    def describir(ce) -> dict:
        return {"id": ce.caso.candidato.id, "nombre": ce.caso.candidato.name}
