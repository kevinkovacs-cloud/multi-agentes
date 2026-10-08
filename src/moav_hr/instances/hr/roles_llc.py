"""
Roles del equipo DAG en el modo LLC — instancia HR (bloque E; sección 6 del handoff).

E2 implementa el rol decisor, el Semantic Matcher (puntos 1 y 2b del pedido):
  · Si (R1): `build_si` del perfil normalizado (skills clave, banda de experiencia,
    educación, antigüedad mínima), sin atributos protegidos (DE-4).
  · A (R2): ADVANCE o REJECT. Operador BIO: la regla del diseñador de `entorno.py`.
  · Sf (R3): {"calificado": sí/no}; en BIO y TBO la etiqueta del escenario de
    entrenamiento, en WIO la revisión humana simulada. Llega después de actuar.
  · u_tarea (R4): 1 si la acción fue la correcta para el resultado observado; 0 si no.
Los demás roles (Parser, Bias Auditor, Explainer) se agregan en E4.
"""
from __future__ import annotations

from moav_hr.instances.hr import entorno
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
