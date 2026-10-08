# E3 · Pre-registro corto: A9 en decisiones

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

Commiteado **antes** de volver a correr la cooperación de P2a. Decisión de Claude chat con delegación de Kevin
(`docs/parada_tecnica/E3_RESPUESTA_ClaudeChat_2026-10-08.md`, opción (c)).

## Cambio

- **A9 (historia mínima del donante) se mide en decisiones, no en ventanas:** un donante puede compartir si tiene
  al menos **20 decisiones propias** (un intervalo) y **los dos grupos** del atributo protegido están representados
  en esas decisiones (sin los dos grupos la LCB no se puede calcular).
- Parámetros en `configs/parada_tecnica.yaml`: `compartir.a9 = decisiones`, `a9_min_decisiones = 20`,
  `a9_ambos_grupos = true`. `m0_historia_minima = 3` (ventanas) se conserva para el código heredado y para la
  corrida original de E3.

## Motivo

Con el gate v2 de Ω (negar solo con evidencia de sesgo, LCB), la cantidad de decisiones ya está en la cota; a A9
solo le queda garantizar que **haya** decisiones de los dos grupos sobre las cuales calcularla. Antes, A9
compensaba el prior r0 = 0,8. En el LLC se coopera entre SARs recién nacidos («la cooperación entre SARs que
cooperan en la layer BIO, entre SARs nacidos que transitan esta layer para alcanzar el estado de evolución de
novato», Ierache 2010, p. 124).

## Qué se corre

Solo la cooperación B ↔ C de P2a (los dos Novice, con estados ganados, tal como están). La colaboración A → B y
los contraejemplos no cambian. Si la cooperación tampoco procede por otro motivo, se reporta y no se cambia nada
más. La corrida original (rechazada por A9 en ventanas) queda en el informe, lado a lado.
