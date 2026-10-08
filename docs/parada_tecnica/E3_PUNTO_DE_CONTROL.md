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

### Cooperación B ↔ C con A9 en decisiones (pre-registro corto, `E3_PREREGISTRO_A9.md`)

- **Resultado:** aceptada — axiomas, can_donate y Ω sin evidencia de sesgo.
- **B en C:** 10 iguales · 3 similares · 3 nuevas; **C en B:** 10 iguales · 1 similar · 1 nueva.
- **Base resultante común a los dos (Alg. 4.9):** sí; ΣP = K: se cumple.
- **Ω en cada sentido:** SemanticMatcher_B: 40 decisiones, LCB 0,000 → sin evidencia de sesgo; SemanticMatcher_C: 20 decisiones, LCB 0,000 → sin evidencia de sesgo.
- Lado a lado con la corrida original: `docs/parada_tecnica/E3_cooperacion_A9_lado_a_lado.md`.

### Qué cambia en la celda de T\* al recibir la experiencia de A

- **Antes de la colaboración:** B elegía REJECT (azar_bio); U por acción: ADVANCE 0,333, REJECT 0,400.
- **Después:** B elige REJECT (celda); U por acción: ADVANCE 0,250, REJECT 0,700.
- **Lectura:** la experiencia que transfiere A, incluida la teoría fallida T\*, baja la utilidad de la acción que fracasó (ADVANCE: 0,333 → 0,250) y le da al novato un plan válido donde antes decidía por azar. En esta corrida B no habría repetido el error de todos modos: su «azar» con el operador BIO ya elegía REJECT.

## Resultados que no fueron los esperados (se reportan tal cual)

1. **La cooperación B ↔ C se rechazó por historia mínima (A9):** SemanticMatcher_B tiene 2 ventanas, SemanticMatcher_C tiene 1 ventana y `can_donate` exige al menos 3. B y C ganan Novice al cierre de un intervalo temprano de BIO, así que llegan a la cooperación con menos ventanas que las que pide A9. Con A9 en decisiones (pre-registro corto) la cooperación se acepta.
2. **Ω no encontró evidencia de sesgo en ningún donante** (LCB = 0,000): misma contracara que en la evolución; con estas historias solo frenaría ante brechas grandes.
3. **El planificador de B no elige T\*** (una teoría fallida) ante un caso con su Si: elige REJECT (celda). Es el uso esperado de una teoría de fracaso: resta utilidad a la acción que fracasó (ver «Qué cambia en la celda de T\*»).

## Para la dirección / para decidir (no se cambió nada)

- **A9 (extensión del modelo, no del LLC):** ¿la historia mínima para donar se mide en decisiones (pre-registro corto de E3) o en ventanas?
- **Pregunta vinculada a la decisión 1 de la hoja:** ¿la evolución y la compartición se condicionan a la ausencia de evidencia de sesgo (implementable a esta escala) o a la evidencia de equidad (reputación certificada, que requiere historias largas)?
