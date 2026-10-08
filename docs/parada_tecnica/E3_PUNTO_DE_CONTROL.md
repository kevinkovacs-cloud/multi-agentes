# E3 · Punto de control del Bloque E (punto 2a del pedido)

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

Rama `eje1/bloque-e`, sin push. Reglas del pre-registro v2 (`E2_PREREGISTRO_v2.md`), commiteado antes de correr.

## E2 v2 (P1 y P2b), con la v1 al lado

- **P1 v2:** estado final **Mature** en 100 ciclos; promociones: ciclo 20: Born → Novice; ciclo 80: Novice → Trained; ciclo 100: Trained → Mature.
- **Comparación lado a lado:** `docs/parada_tecnica/E2_v1_vs_v2.md`. Informes completos (traza, evaluaciones de R7, regla de validez, desacuerdos Fig. 4.21 / Alg. 4.7, resultados no esperados): `docs/parada_tecnica/v1/E2_PUNTO_DE_CONTROL.md` y `docs/parada_tecnica/v2/E2_PUNTO_DE_CONTROL.md`.
- **Característica del gate v2:** `docs/parada_tecnica/p1_gate_caracteristica.png`.

## E3 · Compartición (P2a)

Detalle: `docs/parada_tecnica/v2/p2a_compartir.md`; procedencia: `docs/parada_tecnica/v2/p2a_procedencia.ttl`.

| Equipo | Estado ganado | Ciclos | Ventanas de historia |
|---|---|---|---|
| A | Mature | 100 | 5 |
| B | Novice | 40 | 2 |
| C | Novice | 20 | 1 |

| Operación | Resultado | Motivo | Igual · similar · nueva | ΣP = K |
|---|---|---|---|---|
| Colaboración A → B | aceptada | axiomas, can_donate y Ω sin evidencia de sesgo | 13 · 4 · 23 | se cumple |
| Cooperación B ↔ C | rechazada | rechazada por el código: el par SemanticMatcher_B no puede aportar sin historia de equidad (A9: requiere ≥3 ventanas, tiene 2) | — | — |
| Contraejemplo: cooperación A ↔ B | rechazada | rechazada por el código: la cooperación requiere mismo estado de evolución (Def. 7) | — | — |
| Contraejemplo: colaboración B → A | rechazada | rechazada por el código: el colaborador debe tener nivel estrictamente superior (Def. 8) | — | — |

- **T\*** (ADVANCE, Sf {"calificado": false}): en A (P, K, U) = (1, 1, 0,333); en B = (2, 2, 0,250); prov:wasDerivedFrom: 1; el planificador de B la elige: no (REJECT, celda).
- **T\*✓** (ADVANCE, Sf {"calificado": true}): en A (P, K, U) = (8, 9, 0,818); en B = (11, 13, 0,800); prov:wasDerivedFrom: 1; el planificador de B la elige: sí (ADVANCE, celda).

## Resultados que no fueron los esperados (se reportan tal cual)

1. **La cooperación B ↔ C se rechazó por historia mínima (A9):** SemanticMatcher_B tiene 2 ventanas, SemanticMatcher_C tiene 1 ventana y `can_donate` exige al menos 3. B y C ganan Novice al cierre de un intervalo temprano de BIO, así que llegan a la cooperación con menos ventanas que las que pide A9: con estas reglas, dos Novice recién promovidos no pueden cooperar. La mecánica de la cooperación (base común, ΣP = K) está verificada en `tests/test_bloquee_compartir.py`.
2. **Ω no encontró evidencia de sesgo en ningún donante** (LCB = 0,000): misma contracara que en la evolución; con estas historias solo frenaría ante brechas grandes.
3. **El planificador de B no elige T\*** ante un caso con su Si: elige REJECT (celda). T\* llegó a B con su procedencia, pero en esa celda hay otra teoría con mayor U.

## Para la dirección / para decidir (no se cambió nada)

- **Cooperación y A9.** ¿La historia mínima del donante se mide en ventanas (hoy 3 × 20 ciclos) aunque un agente pueda promover en la primera? Opciones: mantenerlo; que los pares Novice operen en TBO hasta juntar la historia antes de cooperar (requiere pre-registro); o medir A9 en decisiones.
- **Pregunta vinculada a la decisión 1 de la hoja:** ¿la evolución y la compartición se condicionan a la ausencia de evidencia de sesgo (implementable a esta escala) o a la evidencia de equidad (reputación certificada, que requiere historias largas)?
