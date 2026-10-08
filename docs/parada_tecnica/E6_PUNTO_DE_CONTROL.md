# E6 · Punto de control del Bloque E (punto 5 del pedido)

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

Rama `eje1/bloque-e`, sin push. Pre-registro de E6 commiteado antes de correr (`9e346e0`, `docs/parada_tecnica/E6_PREREGISTRO.md`), junto con `E5_RESPUESTA_ClaudeChat_2026-10-08.md`. Documento para la dirección: `docs/parada_tecnica/METRICAS_EQUIDAD_POR_ROL.md`. Datos: `p5_metricas_equidad.json` y `p5_sesgo_programado.json`; figura: `p5_sesgo_programado.png`. Las métricas descriptivas 1 y 2 de E5_RESPUESTA ya están en el informe de E5.

## Qué se hizo

- **Métricas de equidad por rol** en `core/equidad_roles.py` (brecha del resultado favorable, paridad de errores, ê(t) por teoría) y las dos reglas del Auditor sobre un flujo (`auditar_flujo`, con el mismo primitivo que el gate v2).
- **U_rol con α = 1 y α = 0,5** sobre el equipo de E5 con 600 casos; en la corrida con α = 0,5 el planificador registra también qué habría elegido con α = 1 en el mismo estado.
- **Condición con sesgo programado** («parámetros programados»): rasgo proxy `titulo_local` en la Si del Matcher y operador BIO que lo penaliza (regla 11), en dos magnitudes, con el neutro y el Matcher que aprende (α = 1 y α = 0,5).

## Corrida 1: equidad por rol (α = 1 · α = 0,5)

Diferencia de calificados entre grupos en el flujo (tasa base): AR 0,423, no-AR 0,320 (brecha 0,103).

| Rol | Métrica | α = 1 | α = 0,5 | Teorías con ê(t) (m_min = 5 por grupo) |
|---|---|---|---|---|
| Parser | brecha de completitud | 0,003 | 0,003 | 6 de 6 · 10 de 11 |
| Parser | d_TV del canal proxy (cota inferior) | 0,144 | 0,144 | |
| Semantic Matcher | paridad demográfica | 0,123 | 0,123 | 22 de 38 · 25 de 50 |
| Semantic Matcher | paridad de errores (EO) | 0,149 | 0,149 | |
| Bias Auditor | Δ_esc (paridad de derivación) | 0,000 | 0,000 | no aplica (la acción la decide la regla) |
| Explainer | brecha de completitud de la explicación | 0,017 | 0,017 | 4 de 4 · 4 de 4 |

**α = 0,5:** se usó ê(t) en 1250 de 1800 planificaciones (Parser, Matcher y Explainer); la teoría elegida cambió respecto de α = 1 en 175 y la acción en 0. Los aciertos y las tasas favorables por grupo de cada rol son iguales con α = 1 y con α = 0,5. Ejemplos en `METRICAS_EQUIDAD_POR_ROL.md`.

## Paridad demográfica frente a paridad de errores

- **Primeros 260 casos (los de E4):** paridad demográfica 0,154; aciertos 0,761 (AR) y 0,746 (no-AR), es decir, paridad de aciertos pareja; pero las odds igualadas no: TPR 0,825 frente a 0,667 (57 y 45 casos con Sf calificado; z = 1,84, p = 0,066) y FPR 0,288 frente a 0,212: EO 0,158.
- **Los 600 casos:** paridad demográfica 0,123, diferencia de calificados 0,103, aciertos 0,753 y 0,730, EO 0,149 (ΔTPR 0,149, ΔFPR 0,055).
- Lectura: la paridad demográfica sigue a la tasa base; la paridad de aciertos sale pareja; las odds igualadas muestran una diferencia de TPR que, con estos tamaños, no se distingue claramente del azar. Son tres criterios distintos y no coinciden.

## Corrida 2: sesgo programado por un proxy

«Parámetros programados». El Matcher solo sobre los mismos casos; el Auditor sobre sus ventanas de decisiones. Regla (i): ventana de 20. Regla (ii): evidencia acumulada en la capa del Matcher, con δ/L.

| Magnitud | Configuración | Paridad demográfica (toda · por tercio) | EO | Deriva (i) | Deriva (ii) | Estado final | Gate de Ω en la región 7 | Compartición |
|---|---|---|---|---|---|---|---|---|
| detectable (0,40) | neutro | 0,437 · 0,51 / 0,38 / 0,42 | 0,502 | 0 | 24 (desde W07) | Born | — | — |
| detectable (0,40) | α = 1 | 0,160 · 0,18 / 0,14 / 0,16 | 0,121 | 0 | 0 | Novice | nunca negó (LCB máx. 0,000) | aceptada (Ω: brecha 0,160, LCB 0,000) |
| detectable (0,40) | α = 0,5 | 0,160 · 0,18 / 0,14 / 0,16 | 0,121 | 0 | 0 | Novice | nunca negó (LCB máx. 0,000) | aceptada (Ω: brecha 0,160, LCB 0,000) |
| bajo umbral (0,10) | neutro | 0,107 · 0,11 / 0,03 / 0,18 | 0,098 | 0 | 0 | Born | — | — |
| bajo umbral (0,10) | α = 1 | 0,100 · 0,13 / 0,11 / 0,06 | 0,038 | 0 | 0 | Born | nunca negó (LCB máx. 0,000) | rechazada (Ω: brecha 0,100, LCB 0,000; axioma [b]) |
| bajo umbral (0,10) | α = 0,5 | 0,100 · 0,13 / 0,11 / 0,06 | 0,038 | 0 | 0 | Born | nunca negó (LCB máx. 0,000) | rechazada (Ω: brecha 0,100, LCB 0,000; axioma [b]) |

- **d_TV de la Si del Matcher frente al grupo** (cota inferior): 0,767 (detectable) y 0,022 (bajo umbral). La Si no contiene el grupo, pero el rasgo lo deja inferir.
- **(iv) Atenuación** (ilustra el mecanismo; no es evidencia de la conjetura de atenuación): con la magnitud detectable, la paridad demográfica pasa de 0,437 en el neutro a 0,160 en el Matcher que aprende; la diferencia de calificados del flujo es 0,103, así que lo que queda por encima de la tasa base es menor que lo que trae el operador. En BIO y TBO el Matcher prueba primero la acción no probada (P3), así que el operador sesgado decide poco: en promedio actuó en 5,0 % de las decisiones.
- **ê(t) casi no ve el sesgo por proxy:** en las teorías sin título local del Matcher (α = 1, magnitud detectable) hay 17 lecturas de AR y 215 de no-AR en E(t), y 0 de 25 llegan a m_min en los dos grupos. Es la advertencia formal corrida: la disparidad está en qué teorías se aplican a cada grupo, no dentro de una teoría.

## Resultados que no fueron los esperados

1. **α = 0,5 nunca cambia la acción.** Cambió la teoría elegida 175 veces y la acción 0: con U basada en la acción (v2) todas las variantes (Si, A, ·) tienen la misma U y ê(t) solo reordena variantes de la misma acción. Además, en 160 de esos cambios la variante elegida no tenía ê(t) y la de α = 1 sí: el respaldo «sin ê se usa α = 1» favorece a la variante sin evidencia frente a la que tiene ê < 1.
2. **Paridad de aciertos pareja no es paridad de errores.** La lectura del resultado 5 de E4 (0,762 frente a 0,746) vale para los aciertos; las odds igualadas muestran ΔTPR 0,158 en esos mismos casos (p = 0,066). Conviene decir qué criterio es «paridad de errores» para el Matcher.
3. **El Matcher sesgado comparte sin que Ω lo frene.** Con la magnitud detectable, el Matcher que aprende quedó con paridad demográfica 0,160 y su colaboración a un Matcher Born fue aceptada (LCB 0,000 con 300 decisiones por grupo): sus teorías de las celdas sin título local pasan al receptor. Parte de esa brecha es tasa base; el gate de compartición no distingue una de otra.
4. **Con la magnitud bajo umbral el Matcher que aprende no sale de Born:** en BIO su %CEA fue 0,0, 21,7, 10,5, por debajo de %RCE = 25 (con el rasgo en la Si hay el doble de celdas, una causa posible). Su compartición la rechaza el axioma [b]; Ω no tenía evidencia.
5. **La regla acumulada detecta al neutro antes de lo previsto** (desde W07; la característica operativa daba la ventana 16 para una brecha de 0,40 exacta): la brecha realizada en las primeras ventanas fue mayor que la esperada. La regla de ventana (i) no derivó ninguna ventana en ninguna configuración, como estaba previsto.
6. **Bias Auditor:** Δ_esc = 0 por construcción (la derivación es por ventana) y U_rol no aplica (la acción la decide la regla).

## Preguntas para Claude chat (y, si corresponde, para la dirección)

1. **ê(t) por variante o por celda.** Con U(Si, A) de la v2, ¿ê se calcula por celda (Si, A), para que α pueda cambiar la acción? ¿Y qué hacer con las candidatas sin ê(t): usar α = 1 (hoy, que favorece a la variante sin evidencia) o excluirlas del ajuste?
2. **Métrica del Matcher:** ¿paridad de aciertos o odds igualadas (max ΔTPR, ΔFPR)? En los casos de E4 dan cosas distintas.
3. **Gate de compartición:** hoy usa la paridad demográfica de todas las decisiones del donante, con una sola evaluación. No frenó al Matcher sesgado (brecha por debajo de lo detectable con 300 por grupo). ¿Se deja así (es el estándar de evidencia) o se suma una auditoría por celda del rasgo proxy?
4. **Control sin sesgo en la condición programada:** un Matcher que aprende, sin el rasgo ni el operador sesgado, sobre los mismos casos, separaría la tasa base del sesgo residual. No estaba pre-registrado; ¿se agrega en E7?

## Qué sigue

E7 (`generar_todo.py`, informe final, `LEEME_REUNION.md`, ESTADO). **Frenado en el punto de control de E6.** Sin push.

