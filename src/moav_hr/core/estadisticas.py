"""
Estadísticas de aprendizaje de la región 6 del LLC — bloque E · E2.4 (G8).

Fuente: Ierache (2010), §4.2 (p. 63) y §4.4.9 (pp. 117–122, Fig. 4.27). Por ciclo y por
intervalo de n ciclos se registran: situaciones distintas, teorías acumuladas, teorías por
intervalo de utilidad (0,01 < U ≤ 0,25; 0,25 < U ≤ 0,5; 0,5 < U ≤ 0,75; 0,75 < U ≤ 1,
p. 120), teorías exitosas (U > 0,75), teorías nuevas, ciclos exitosos (el ciclo termina con
una teoría de U > 0,75, p. 118), planes, planes exitosos (la situación final observada es la
de la teoría del plan, Fig. 4.17), azares y la relación P/K por intervalo de U (Tabla 4.4).

Declaraciones: con U binaria (u_tarea ∈ {0, 1}) las teorías con U = 0 no caen en ningún
intervalo (el primero empieza en 0,01, como en la fuente). «P/K general» se informa como el
promedio de P/K sobre todas las teorías [interpretación de «producto de la suma de los
valores obtenidos en cada rango», p. 120]. Las teorías recibidas por compartición no cuentan
como nuevas (P1). Genérico: no importa `instances/`.
"""
from __future__ import annotations
from typing import Hashable

from moav_hr.core.theory import TheoryBase

INTERVALOS_U = ((0.01, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 1.0))


class EstadisticasLLC:
    def __init__(self, umbral_exitoso: float = 0.75):
        self.umbral_exitoso = umbral_exitoso
        self.situaciones: set[Hashable] = set()
        self.ciclos = 0
        self.ciclos_exitosos = 0
        self.teorias_nuevas = 0
        self.planes = 0
        self.planes_exitosos = 0
        self.azares = 0

    def registrar_ciclo(self, qsi: Hashable, tipo_registro: str, u: float, es_azar: bool,
                        plan_valido: bool, plan_exitoso: bool) -> bool:
        """Registra el ciclo; devuelve si fue exitoso (U > umbral)."""
        self.ciclos += 1
        self.situaciones.add(qsi)
        exitoso = u > self.umbral_exitoso
        self.ciclos_exitosos += exitoso
        self.teorias_nuevas += tipo_registro in ("nueva", "similar")
        self.azares += es_azar
        self.planes += plan_valido
        self.planes_exitosos += plan_exitoso
        return exitoso

    def instantanea(self, base: TheoryBase) -> dict:
        ts = base.theories
        por_u, pk_por_u = [], []
        for a, b in INTERVALOS_U:
            en = [t for t in ts if a < t.u <= b]
            por_u.append(len(en))
            pk_por_u.append(round(sum(t.p / t.k for t in en) / len(en), 4) if en else None)
        return {
            "ciclos": self.ciclos, "situaciones": len(self.situaciones),
            "teorias_acumuladas": len(ts),
            "teorias_por_intervalo_u": por_u,
            "teorias_exitosas": sum(1 for t in ts if t.u > self.umbral_exitoso),
            "teorias_nuevas": self.teorias_nuevas,
            "ciclos_exitosos": self.ciclos_exitosos,
            "planes": self.planes, "planes_exitosos": self.planes_exitosos,
            "azares": self.azares,
            "pk_por_intervalo_u": pk_por_u,
            "pk_general": round(sum(t.p / t.k for t in ts) / len(ts), 4) if ts else None,
        }
