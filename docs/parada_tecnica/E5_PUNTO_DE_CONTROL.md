# E5 · Punto de control del Bloque E (punto 3 del pedido)

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

Rama `eje1/bloque-e`, sin push. Pre-registro de E5 commiteado antes de correr (`dd0d20a`, `docs/parada_tecnica/E5_PREREGISTRO.md`), junto con `E4_RESPUESTA_ClaudeChat_2026-10-08.md`. Los resultados de E4 quedan como están. Detalle de la corrida: `docs/parada_tecnica/p3_equipos.md` y `p3_equipos.json`; figura: `docs/parada_tecnica/p3_maduracion_equipos.png`.

## Qué se corrió

Seis equipos DAG con las reglas de E5: Bias Auditor sin estados, exploración en WIO solo para el Explainer y Si del Explainer tipo · destinatario. A es el flujo de E4; B recibe colaboración de A rol por rol al nacer; B0 procesa los mismos casos sin compartir; BC procesa los mismos casos y coopera con C en Novice; N es el SAR neutro de L-3. Los estados se ganan: ninguno se fija a mano.

## Colaboración A → B

- **Parser** (mature → born): aceptada; 0 iguales, 0 similares, 16 nuevas; base de B 0 → 16; ΣP = K en B: sí; LCB de Ω sobre A 0,000.
- **Semantic Matcher** (trained → born): aceptada; 0 iguales, 0 similares, 69 nuevas; base de B 0 → 69; ΣP = K en B: sí; LCB de Ω sobre A 0,000.
- **Explainer** (mature → born): aceptada; 0 iguales, 0 similares, 9 nuevas; base de B 0 → 9; ΣP = K en B: sí; LCB de Ω sobre A 0,000.

## Cooperación BC ↔ C

- **Parser:** aceptada al cierre de BIO-W01 (8 iguales, 2 similares, 0 nuevas; ΣP = K en los dos: sí).
- **Semantic Matcher:** no hubo cooperación. Ventanas con BC en Novice: BIO-W01 (C en Born); el rol de C nunca estuvo en Novice en esas ventanas (axioma [a]).
- **Explainer:** aceptada al cierre de BIO-W01 (4 iguales, 0 similares, 0 nuevas; ΣP = K en los dos: sí).

## ¿B madura antes que B0?

Ciclo del rol en que gana cada estado (en los roles por caso, casos procesados):

| Rol | Estado | A | B | B0 | BC | C |
|---|---|---|---|---|---|---|
| Parser | Novice | 20 | 20 | 20 | 20 | 20 |
| Parser | Trained | 40 | 40 | 40 | 40 | 40 |
| Parser | Mature | 60 | 60 | 60 | 60 | 60 |
| Semantic Matcher | Novice | 40 | 40 | 20 | 20 | — |
| Semantic Matcher | Trained | 120 | 80 | 40 | 40 | — |
| Semantic Matcher | Mature | — | 100 | — | — | — |
| Explainer | Novice | 20 | 20 | 20 | 20 | 20 |
| Explainer | Trained | 40 | 40 | 40 | 40 | 40 |
| Explainer | Mature | 60 | 60 | 60 | 60 | 60 |

| Rol | Ciclos exitosos (B · B0 · BC · N) | Teorías nuevas propias (B · B0 · BC · N) |
|---|---|---|
| Parser | 241 · 238 · 238 · 122 | 0 · 15 · 14 · 9 |
| Semantic Matcher | 204 · 173 · 173 · 156 | 6 · 60 · 60 · 39 |
| Explainer | 260 · 255 · 258 · 37 | 0 · 9 · 4 · 4 |

La región 7 se evalúa al cierre de cada intervalo de 20 ciclos, así que lo más rápido posible es Novice en el ciclo 20, Trained en el 40 y Mature en el 60.

## Cálculo literal de L-3 entre configuraciones

En la tesis, los porcentajes se determinan comparando configuraciones de SAR (Anexo L-3, Tablas L-16 y L-17). Para decidir la promoción de un agente individual durante su actuación se operacionalizan como en P1; acá se calculan como en la fuente, entre configuraciones que procesan los mismos casos (N, B0, B y BC; mínimo = N).

| Rol | Evaluada | %CEA | %RCE | %TNA | %RTN | Evoluciona |
|---|---|---|---|---|---|---|
| Parser | B | 97,5 | 71,9 | 100,0 | 100,0 | sí |
| Parser | BC | 95,1 | 71,9 | -47,4 | 6,7 | sí |
| Semantic Matcher | B | 30,8 | 13,1 | 85,5 | 90,0 | sí |
| Semantic Matcher | BC | 10,9 | 13,1 | -45,5 | 0,0 | no |
| Explainer | B | 602,7 | 447,3 | 100,0 | 100,0 | sí |
| Explainer | BC | 597,3 | 447,3 | 5,9 | 55,6 | sí |

**Nota técnica para conversar con Jorge.** Con estas definiciones, %TNA ≤ %RTN equivale a «promedio de teorías nuevas ≤ máximo», y %CEA ≥ %RCE, a «ciclos exitosos de la configuración evaluada ≥ promedio de las configuraciones». Con B, que no generó teorías propias en el Parser ni en el Explainer, %TNA = %RTN = 100.

## Equidad por rol

- **Canal proxy del Parser.** Con el operador BIO (neutro N), la completitud fue 0,585 (AR) y 0,354 (no-AR): brecha 0,231 (esperada por el pre-registro de E4: 0,180). Con aprendizaje, la brecha de toda la corrida fue 0,085 en B y 0,077 en B0; fair(W) del Parser en las tres primeras ventanas: B 0,9, 1,0, 0,8; B0 1,0, 1,0, 0,8. Lo que queda son los documentos con defecto (regla 7): en este flujo, 4/130 en AR y 15/130 en no-AR (Fisher p = 0,0151). Es otra diferencia de la semilla: en 200 semillas más del mismo generador, 10,0 % y 10,3 % (p = 0,3605). Esto no es evidencia de la conjetura de atenuación.
- **fair(W) media · mínimo por rol** (B · B0): Parser 0,900 · 0,7 frente a 0,908 · 0,7; Semantic Matcher 0,800 · 0,7 frente a 0,815 · 0,6; Explainer 1,000 · 1,0 frente a 0,977 · 0,8. El Bias Auditor no derivó ninguna ventana en ningún equipo (ventana de 20; decisión 2).

## Celdas nunca resueltas

- **A:** Parser 0; Semantic Matcher 3 (9 fracasos); Explainer 0.
- **B:** Parser 0; Semantic Matcher 3 (8 fracasos); Explainer 0.
- **B0:** Parser 0; Semantic Matcher 8 (35 fracasos); Explainer 0.
- **BC:** Parser 0; Semantic Matcher 8 (35 fracasos); Explainer 0.
- **C:** Parser 0; Semantic Matcher 4 (18 fracasos); Explainer 0.
- El Explainer de A, con las reglas de E5, no tiene celdas nunca resueltas; en E4 tenía 1 (48 fracasos en WIO). Es el hallazgo que motivó la decisión 3.

## Pedido sobre el resultado 5 de E4

Calificados en el flujo de E4: 0,446 (AR) y 0,300 (no-AR). z = 2,44; Fisher exacto p = 0,0208; permutación p = 0,0206. En 200 semillas más, la diferencia media es -0,0012 y solo 2,0 % de las semillas tiene una diferencia de igual o mayor tamaño. Con todas juntas, el grupo es independiente de la verdad (Fisher p = 0,7815) y de la celda de Si (χ² p = 0,1583). Detalle: `docs/parada_tecnica/e4_muestreo_calificados.md`. La semilla no se cambió.

## Métricas descriptivas agregadas después del punto de control (E5_RESPUESTA, decisiones 1 y 2)

Calculadas sobre las mismas corridas de E5: `p3_descriptivas.py` las reconstruye en memoria y verifica que `p3_equipos.json` sale idéntico byte a byte antes de medir. No cambian ninguna regla ni ninguna promoción. Datos: `p3_descriptivas.json`; figura: `p3_curvas_aprendizaje.png`.

### 1 · Desempeño frente al equipo neutro N

Para la promoción (región 7) se mantiene el contrafáctico sobre las propias entradas del rol, como está pre-registrado: aísla lo que aprendió ese agente. Para comparar equipos se agrega esta métrica: aciertos de cada rol con las entradas de su propio equipo, frente a los del rol neutro con las entradas del equipo neutro (mismos 260 casos). «Equipo» = casos resueltos de punta a punta (perfil completo, decisión correcta y explicación completa).

| Rol | N | B | B0 | BC |
|---|---|---|---|---|
| Parser | 122 | 241 (+97,5 %) | 238 (+95,1 %) | 238 (+95,1 %) |
| Semantic Matcher | 156 | 204 (+30,8 %) | 173 (+10,9 %) | 173 (+10,9 %) |
| Explainer | 37 | 260 (+602,7 %) | 255 (+589,2 %) | 258 (+597,3 %) |
| Equipo | 21 | 190 (+804,8 %) | 158 (+652,4 %) | 160 (+661,9 %) |

> «La regla de evolución mide lo que aprende cada agente, no el resultado del equipo; cuando un rol de arriba mejora, el de abajo tiene que superar una referencia más exigente.»

El Matcher de B promovió más lento que el de B0 porque su vara era más alta. Aun así, el equipo B acertó más que B0 (204 frente a 173 decisiones correctas; 190 frente a 158 casos resueltos de punta a punta) y solo el Matcher de B llegó a Mature.

### 2 · Curvas de aprendizaje sin piso

> «Con intervalos de 20 ciclos, la promoción tiene un piso de 20 ciclos por estado; para Parser y Explainer ese piso domina y la colaboración no puede adelantarla. Las curvas muestran el efecto que el piso oculta.»

| Rol | Ciclos exitosos al ciclo 20 (B · B0 · C) | Teorías nuevas al ciclo 20 (B · B0 · C) | Al final (B · B0 · C) |
|---|---|---|---|
| Parser | 19 · 16 · 15 | 0 · 10 · 9 | 241 exitosos, 0 nuevas · 238 exitosos, 15 nuevas · 227 exitosos, 13 nuevas |
| Semantic Matcher | 17 · 16 · 10 | 0 · 11 · 15 | 204 exitosos, 6 nuevas · 173 exitosos, 60 nuevas · 204 exitosos, 63 nuevas |
| Explainer | 20 · 18 · 15 | 0 · 4 · 9 | 260 exitosos, 0 nuevas · 255 exitosos, 9 nuevas · 255 exitosos, 9 nuevas |

**Primer ciclo en que se cumpliría la regla** si se evaluara en cada ciclo (acumulada en la capa, como la v2), y desde qué ciclo se cumple sin interrupción hasta el cierre real. Descriptivo: la promoción real sigue siendo al cierre. Con muy pocos ciclos la regla es inestable (un acierto frente a un fallo del operador BIO ya da %CEA = 100), por eso se informa también el cumplimiento sostenido.

| Equipo | Rol | Capa: primer ciclo · sostenido desde · promoción real |
|---|---|---|
| A | Parser | BIO: 5 · 10 · 20; TBO: 1 · 1 · 20; WIO: 1 · 1 · 20 |
| A | Semantic Matcher | BIO: 9 · 28 · 40; TBO: 1 · 69 · 80; WIO: 16 · — · — |
| A | Explainer | BIO: 7 · 7 · 20; TBO: 1 · 1 · 20; WIO: 1 · 1 · 20 |
| B | Parser | BIO: 5 · 5 · 20; TBO: 2 · 2 · 20; WIO: 2 · 2 · 20 |
| B | Semantic Matcher | BIO: 1 · 24 · 40; TBO: 9 · 21 · 40; WIO: 1 · 20 · 20 |
| B | Explainer | BIO: 4 · 4 · 20; TBO: 1 · 1 · 20; WIO: 1 · 1 · 20 |
| B0 | Parser | BIO: 6 · 11 · 20; TBO: 2 · 2 · 20; WIO: 2 · 2 · 20 |
| B0 | Semantic Matcher | BIO: 1 · 1 · 20; TBO: 7 · 12 · 20; WIO: — · — · — |
| B0 | Explainer | BIO: 10 · 19 · 20; TBO: 4 · 4 · 20; WIO: 1 · 1 · 20 |
| BC | Parser | BIO: 6 · 11 · 20; TBO: 2 · 2 · 20; WIO: 2 · 2 · 20 |
| BC | Semantic Matcher | BIO: 1 · 1 · 20; TBO: 7 · 12 · 20; WIO: — · — · — |
| BC | Explainer | BIO: 10 · 19 · 20; TBO: 1 · 1 · 20; WIO: 1 · 1 · 20 |
| C | Parser | BIO: 4 · 4 · 20; TBO: 1 · 1 · 20; WIO: 3 · 3 · 20 |
| C | Semantic Matcher | BIO: 9 · — · — |
| C | Explainer | BIO: 5 · 5 · 20; TBO: 2 · 2 · 20; WIO: 1 · 1 · 20 |

En BIO, la regla se cumple sin interrupción desde el ciclo 5 en el Parser de B y desde el 11 en el de B0; en el Explainer, desde el 4 y el 19. Es el efecto de la colaboración que el piso de 20 ciclos oculta en la promoción.

### 3 · El Matcher de C no coopera

Es el axioma funcionando: solo cooperan SAR en el mismo estado (§4.3.1 [a], p. 70). El Matcher de C no superó al neutro en BIO, siguió en Born y no puede cooperar con un Novice. La cooperación entre Matchers ya está demostrada en P2a (E3, con A9 en decisiones). En E5 la cooperación de equipo se ve en Parser y Explainer.

## Resultados que no fueron los esperados

1. **El Matcher de B gana Novice y Trained más tarde que el de B0** (Novice en el ciclo 40 frente a 20; Trained en el 80 frente a 40), **pero llega a Mature** (ciclo 100) y el de B0 queda en Trained. En la primera evaluación, B acertó 17 de 20 frente a 16 de B0, pero su CE_0 fue 14 frente a 11: %CEA 21,4 frente a 45,5. CE_0 es el operador BIO sobre la Si que le llega al Matcher, y en B esa Si viene de un Parser que ya extrae bien desde el primer caso (recibió las teorías de A). Un Parser mejor sube el punto de comparación del Matcher. En toda la corrida, el Matcher de B acertó 204 frente a 173 de B0.
2. **Parser y Explainer ganan cada estado en el primer cierre posible en todos los equipos** (B, B0, BC y C), así que la colaboración no puede adelantarlos: el efecto se ve en los aciertos y en las teorías nuevas, no en los ciclos hasta cada estado.
3. **El Matcher de C nunca sale de Born** (agota los 60 ciclos de BIO con %CEA -9,1, 0,0, 5,1). Por eso no hubo cooperación del Matcher, y el Matcher de BC es el mismo que el de B0 (173 y 173 ciclos exitosos). En L-3 con BC como configuración evaluada, el Matcher no cumple %CEA ≥ %RCE.
4. **La colaboración no cierra el canal proxy del Parser antes que B0:** B0 lo cierra por sí solo en el primer intervalo; la brecha que queda en los dos viene de los documentos con defecto de esta semilla (ver «Equidad por rol»).
5. **La semilla de E4 es poco frecuente** (p ≈ 0,02): la brecha de paridad del Matcher en E4 viene de una diferencia de calificados que aparece en pocas semillas.

## Preguntas para Claude chat (y, si corresponde, para la dirección)

Respondidas en `docs/parada_tecnica/E5_RESPUESTA_ClaudeChat_2026-10-08.md` (ver las métricas descriptivas de arriba). Queda para el encuentro: ¿la evolución de un agente dentro de un equipo se mide contra sus propias entradas o contra el equipo neutro?

1. **Punto de comparación de %CEA dentro de un equipo** (resultado 1). Hoy CE_0 es el operador BIO sobre la Si que le llega al rol, así que el aprendizaje de un rol de arriba sube la vara del de abajo. ¿Se mantiene (es el contrafáctico pre-registrado) o, para comparar equipos, se informa también contra el equipo neutro N?
2. **Efecto techo de la promoción por intervalos** (resultado 2). Con n = 20, Parser y Explainer ya promueven en cada primer cierre posible sin compartir. ¿Se informa así, o se agrega una métrica de maduración que no tenga piso (por ejemplo, ciclos hasta una tasa de aciertos dada)? No se cambia nada sin decisión.
3. **Cooperación del Matcher** (resultado 3). No se cambia la semilla de C. ¿Se informa tal cual?
4. **E6:** se sigue con la condición de control con sesgo programado pre-registrada en E4_RESPUESTA (decisión 2), salvo indicación en contrario.

## Qué sigue

E6 (métricas de equidad por rol, con la condición de sesgo programado) y E7 (informe y cierre). **Frenado en el punto de control de E5.** Sin push.

