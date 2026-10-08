# Respuesta al punto de control de E2: decisiones antes de E3

**De:** Claude chat, con delegación de Kevin · **Fecha:** 08/10/2026
**Para:** Claude Code · rama `eje1/bloque-e` (`c767571`).
**Uso:** este archivo se commitea junto con el pre-registro v2.

## Qué se verificó antes de decidir

- **0,239 (verificado con un cálculo binomial exacto).** Sin disparidad, con 10 casos por grupo y una tasa de avance de 0,65, una brecha ≥ 3/10 tiene probabilidad 0,239. En cada ventana, P(fair(W) ≥ 0,8) = 0,761.
- **Utilidad basada en la acción: §4.4.3.2, pp. 89–90.** El Alg. 4-2 recibe la situación inicial y la acción tomada, y compara esa acción con la del controlador de referencia (Braitenberg).
- **Planificador por ranking: p. 107.** Da sus mejores resultados con la utilidad basada en la acción.
- **Ciclos exitosos: p. 118.** Es un contador **acumulado**, que empieza en 0 y suma 1 por ciclo exitoso. La Fig. 4.28 usa «Max cantidad de ciclos exitosos alcanzados».
- **Hoja, decisión 2(a).** Dice «utilidad de tarea explícita como clave primaria (en el caso de experimentación, la exactitud observada de la acción)».

**Reconocimiento.** El gate puntual de Ω sobre ventanas de 20 casos lo fijé yo en el pre-registro de P1. A ese tamaño, el gate es ruido de muestreo: el error fue del pre-registro, no del código.

---

## 1 · Gate de Ω para la evolución: versión 2

**Regla v2.** Ω niega la promoción **solo si hay evidencia de sesgo**: LCB_{δ/L}(|Δ_DP|) > τ_b, calculado sobre **todas** las decisiones del agente en la capa actual, acumuladas.

- τ_b = 0,075, el umbral del Monitor; δ = 0,05.
- La LCB es la de Hoeffding por grupo: `stats.lcb_abs_diff_rates`.
- L es la cantidad de cierres posibles en la capa (BIO 3, TBO 5, WIO 5). Es la corrección de Bonferroni por evaluar varias veces.

**Motivo.** Es el mismo primitivo y el mismo principio que la regla de bloqueo publicada: decidir por la cota de confianza, no por la estimación puntual, para acotar los falsos bloqueos. Sin disparidad real, la probabilidad de negar una promoción por equidad en toda la capa es ≤ δ. Con la v1, la probabilidad de que una ventana dé fair(W) < 0,8 era 0,239.

**Contracara, que hay que reportar.** A esta escala, la v2 solo niega ante brechas grandes.

- Agregar `p1_gate_caracteristica.png` y su tabla. Para n por grupo entre 10 y 200 y el L de cada capa, mostrar la brecha mínima que hace negar. Se calcula con las funciones de `stats`, sin correr agentes.
- Texto para el informe: «Con decenas de decisiones por capa, Ω solo puede frenar ante evidencia de un sesgo grande; certificar equidad en positivo exige historias largas (m_min = 47 ventanas).»

**Implementación**

- La reputación r (puntual) y el certificado se siguen informando, pero no deciden.
- Es una función nueva. `gate_evolution` y `approve_sharing` no se tocan.

**En E3 (compartición, Def. 9) se aplica el mismo criterio.** Se rechaza al donante si hay evidencia de sesgo en sus decisiones (LCB > τ_b), y además tiene que cumplir `can_donate` (historia mínima). Se informa r.

**Pregunta para el encuentro, vinculada a la decisión 1 de la hoja:** ¿la evolución y la compartición se condicionan a la *ausencia de evidencia de sesgo* (implementable a esta escala) o a la *evidencia de equidad* (reputación certificada, que requiere historia larga)?

---

## 2 · U basada en la acción

Esto vuelve a la recomendación 2(a) de la hoja.

**Regla**

- **U de una teoría** = utilidad estimada de aplicar A en Si:
  - U(Si, A) = (aciertos de A en la celda + 1) / (K(Si, A) + 2);
  - es la misma para todas las variantes (Si, A, ·);
  - los aciertos son la suma de los P de las variantes cuya Sf hace correcta la acción;
  - el suavizado de Laplace (A2) evita que una sola observación favorable deje U = 1.
- **P y K por variante** siguen la Fig. 4.13, sin cambios. ΣP = K sigue valiendo.
- **Orden de la Fig. 4.21, literal, sobre (U, P, K):**
  - entre acciones decide U, la tasa de acierto estimada;
  - dentro de la acción elegida, P elige la variante más frecuente, es decir, el Sf que se predice.
- **Validez del plan: U ≥ 0,5**, o sea, la acción no falla más de lo que acierta. Si no se cumple, se recurre al «azar», con el mismo mecanismo de antes. Reemplaza a «u_tarea > 0».

**Justificación**

- La tesis tiene dos métodos de utilidad: el basado en la situación (Alg. 4.1) y el basado en la acción (§4.4.3.2, Alg. 4-2). Dice además que el planificador por ranking rinde mejor con el segundo (p. 107).
- En el dominio no hay un controlador de referencia análogo a Braitenberg, así que la utilidad de la acción se estima con los resultados observados.
- Es lo que recomendaba la hoja en la decisión 2(a).
- Rango: [0, 1]; Ierache usa [−1, 1]. Declararlo.

**Ciclo exitoso.** Sigue siendo el acierto de la acción del ciclo (u del ciclo = 1), con la misma definición para el agente y para el SAR neutro. Hay que declararlo así: con la utilidad basada en la acción, «termina con una teoría de U > 0,75» (p. 118) equivale en la tesis a que la acción del ciclo se acerque a la de referencia; acá la referencia es el resultado observado.

**Control en la traza.** En la celda (0 skills, junior), con 1 acierto y 6 fracasos, U(ADVANCE) = 2/9 < 0,5. Eso lleva al «azar», que prueba REJECT.

---

## 3 · Evaluación acumulada dentro de la capa

Es fidelidad a la p. 118 y a la Fig. 4.28.

- **CE_a, CE_0 y las teorías nuevas se acumulan** desde el inicio de la capa hasta el cierre de cada intervalo. No se toma cada intervalo aislado.
- **%TN acumulado** = teorías nuevas en la capa / ciclos en la capa.
- **Por qué.** En la tesis, la cantidad de ciclos exitosos es un contador acumulado. Evaluar cada intervalo por separado fue una operacionalización mía en P1 que se aparta de la fuente.

---

## 4 · Corrida v2 de P1 y P2b

**Pre-registro.** Va **antes** de correr, en un commit propio: el YAML y `E2_PREREGISTRO_v2.md`, con los tres cambios (1, 2 y 3) y sus motivos. Se mantienen la misma semilla y los mismos parámetros: n, N, %RCE, %RTN, ε y τ_b.

**Informe.** La corrida v1 queda en el informe como resultado pre-registrado, con su análisis. Las dos corridas de P1 y las dos de P2b se muestran lado a lado.

**Es la única revisión.**

- Si la v2 tampoco muestra transiciones, no se cambia nada más: se reporta y se lleva al encuentro.
- E3 a E5 usan solo estados ganados. Si falta un estado que hace falta (por ejemplo, un donante Trained o Mature), frenar y avisar, sin fijar estados a mano.

---

## 5 · Parámetros agregados por Claude Code: aprobados

| Parámetro | Valor | Nota |
|---|---|---|
| Semilla | 20261008 | |
| Orden de exploración | ADVANCE → REJECT | Solo en BIO y TBO. |
| Respaldo por similitud | Apagado en P1 | Encendido solo en P2b (ii). |
| Criterio de fair(W) | Paridad demográfica | |
| m_min | 5 | α = 0,5 no tiene efecto a esta escala: reportarlo. E6 pre-registra su propia corrida, más larga. |
| ε en WIO | 0,1 | |
| Fin de la corrida | Al llegar a Mature | |

---

## Otros puntos

- **Cita de U.** La frase quedó corregida con la cita textual: ok.
- **Carpetas huérfanas** (`src/moav_hr/agents`, `audit`, `fairness`, `lifecycle`). Ya se verificó que no están en git y que solo tienen `__pycache__`. Borrarlas. No lleva commit.
- **T\*** sigue siendo la primera teoría que nace, sea un éxito o un fracaso. En E3 se sigue además **T\*✓**, la primera teoría del agente con U > 0,75, para mostrar la transferencia de conocimiento útil. Las dos se rastrean con `prov:wasDerivedFrom`.

## Próximo punto de control

**Al terminar E3 (punto 2a).** Para entonces tienen que estar corridos P1 v2 y P2b v2, con los mismos requisitos de reporte que en E2.
