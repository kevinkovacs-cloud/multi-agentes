"""
Núcleo genérico del modelo (independiente del dominio).

Implementa el modelo formal de la propuesta v13 §2 / §2bis:
  - ciclo de vida individual del agente (Def. 2) y las 7 regiones (§3)
  - teorías ⟨Si, A, Sf, P, K, U⟩ con equivalencia por cuantización (Def. 3) y
    selección por ranking (Def. 4)
  - operadores de compartición: cooperación (Def. 7) y colaboración (Def. 8),
    condicionados por reputación de equidad (Def. 9)
  - Monitor de Utilidad de Equidad Ω (§2.4)
  - métricas de equidad por ventana y amplificación μ / diversidad D (Def. 5,6,10,11)
  - orquestación del DAG (Def. 1) y ontología/audit trail RDF (§2.5)

REGLA DE DECOUPLING (no negociable): `core/` NO importa nada de `instances/`.
"""
__all__ = ["lifecycle", "theory", "fairness", "sharing", "retrieval",
           "agent", "monitor", "orchestrator"]
