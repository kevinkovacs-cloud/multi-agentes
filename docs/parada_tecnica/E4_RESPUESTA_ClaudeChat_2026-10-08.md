# Respuesta al punto de control de E4: decisiones antes de E5

**De:** Claude chat, con delegación de Kevin. **Fecha:** 08/10/2026. **Rama:** `eje1/bloque-e` (`f321bce`).

Este archivo se commitea junto con el pre-registro de E5.

## Criterio general

**Los resultados de E4 quedan como están.** Son el resultado pre-registrado del punto 4 y **no** se vuelve a correr P4. Los cambios de abajo valen desde E5 en adelante. Van en el pre-registro de E5, con su motivo, antes de correr. Ninguno es un ajuste de parámetros numéricos.

---

## 1 · Evolución del Bias Auditor → opción (a)

**Decisión.** El Bias Auditor **no tiene estados ganados**: es un rol supervisor de configuración BIO fija, igual que el Orchestrator (DE-7). Lo que conserva y lo que no aplica:

- **Conserva:**
  - su base de teorías, que son las «teorías de sesgo» para auditoría (Ierache, 17/07/2026);
  - las regiones 1 a 6;
  - las estadísticas de la región 6.
- **No aplica:** la región 7.

**Motivo.** En el LLC, evolucionar es mejorar el rendimiento del aprendizaje (§4.4.10). Por DE-6, la acción del Auditor la fija la regla certificada, que no aprende. Por construcción, no hay rendimiento que pueda mejorar. Es coherente con el artículo: Ω condiciona la evolución de los demás, no la propia.

- No se inventa un criterio propio (opción b): sería una extensión sin respaldo en la fuente.
- No se muestra como «límite» (opción c): no es un límite, es el diseño.

**En el informe:** «El Bias Auditor no evoluciona porque su regla de intervención es regulatoria (BIO) y no se aprende; registra teorías de sesgo para auditoría.»

**Pregunta para la dirección:** ¿Ω debe tener un ciclo de vida propio? La propuesta es que no.

---

## 2 · Ventana del Auditor → se mantiene en 20 en E5

**Decisión.** En E5 se mantiene la ventana de 20, coherente con fair(W). Que no derive es **correcto**. Las dos cosas que hay que reportar:

- **El escenario no tiene sesgo real:** el grupo se asigna independiente de la Si y de la verdad. Derivar sería un falso bloqueo.
- **Con 10 casos por grupo la regla tampoco podría derivar** aunque hubiera sesgo: la LCB máxima es 0,0638 < τ_b. Es la misma conclusión que la característica operativa del gate (E2 v2).

**En E6, para que las métricas de equidad no queden todas en cero sin demostrar nada,** se pre-registra una condición de control con **sesgo programado**, con el rótulo «parámetros programados» igual que en D5. Por ejemplo, un operador BIO del Matcher que penaliza a un grupo. En esa condición se muestran lado a lado:

- (i) la regla del Auditor con la ventana de 20;
- (ii) la regla con evidencia **acumulada en la capa**, con corrección por evaluaciones repetidas (δ/L), igual que el gate v2. Con esta variante, Ω deriva la ventana en curso cuando la cota acumulada supera τ_b.

El objetivo es mostrar **cuándo** el mecanismo puede actuar y cuándo no. No es ajustar nada para que derive.

---

## 3 · Exploración en WIO → solo para el Explainer

**Criterio:** en WIO se puede explorar **solo si la acción del rol no puede cambiar la decisión sobre la persona**. La decisión P3 («azar» solo en BIO y TBO) se mantiene para el resto.

| Rol | ¿Explora en WIO? | Por qué |
|---|---|---|
| Explainer | Sí | Actúa **después** de la decisión. Si no hay plan válido (U < 0,5), en WIO prueba la primera acción no probada en la celda, igual que en BIO y TBO. Seguir entregando una explicación que se sabe incompleta también perjudica: el regulador o el usuario no recibe lo que necesita. |
| Parser | No | Su estrategia cambia la Si que percibe el Matcher. Un perfil fallido lleva a una decisión peor sobre la persona. |
| Matcher | No | Decide sobre la persona. |

**No se exige cobertura de celdas para promover.** La regla de evolución del LLC mira el agregado (§4.4.10), no la cobertura. En cambio, el informe reporta por rol las **celdas nunca resueltas** (celdas con fracasos y sin un plan válido al final).

**En el informe:** el resultado 2 de E4 (Explainer 48/48 en «rechaza · regulador · varios») queda como hallazgo que motivó este criterio.

---

## 4 · Cada rol transita su propia capa → aceptado

En el DAG, los roles comparten el caso pero no el estado. Se declara como adaptación: en el LLC cada SAR tiene un escenario por capa (§4.2, p. 62). El escenario solo fija qué casos llegan.

---

## 5 · Canal proxy del Parser → se mantiene

Se mantiene en E5 y E6. Es lo que vuelve no trivial la equidad del Parser: con el operador BIO, la brecha de completitud esperada es de 0,180. Además es realista: el formato del CV puede correlacionar con el origen.

Que el Parser lo cierre en el primer intervalo **es un resultado**, y hay que contarlo así: el aprendizaje de la estrategia por plantilla elimina una brecha inducida por un proxy.

En E5 se mide si el equipo B, con colaboración, la cierra antes que B0. Tiene que quedar dicho que esto no es evidencia de la conjetura de atenuación.

---

## 6 · «Motivos» en la Si del Explainer → se saca desde E5

**Decisión.** Desde E5, la Si del Explainer queda como **tipo · destinatario** (6 celdas en vez de 12).

**Motivo.** El pre-registro de E4 ya mostraba, **antes de correr**, que «motivos» no cambia la mejor estrategia en ninguna celda. Lo puse yo en la sección 6 del handoff y solo parte celdas, lo que demora el aprendizaje (resultado 2 de E4). Se declara como corrección del diseño de la Si, sin relación con números.

---

## Otros pedidos

- **Resultado 5 de E4 (brecha de paridad del Matcher, 0,154).** Documentar en el informe que la diferencia de tasas de calificados entre grupos (0,446 frente a 0,300, con 130 por grupo) es una fluctuación de muestreo de la semilla:
  - informar el estadístico (z ≈ 2,4) y un test exacto o de permutación;
  - verificar con un test de independencia que el generador asigna el grupo independiente de la Si y de la verdad, como dice la regla 5.

  **No cambiar la semilla.** Es un buen ejemplo de que la paridad demográfica marca brechas que vienen de las tasas base, mientras la paridad de errores (0,762 frente a 0,746) no las muestra. Sirve para E6.
- **CE_0 contrafáctico (resultado 1).** La corrección fue antes de la corrida oficial y es la definición pre-registrada: ok. Dejarlo explícito en el informe final.
- **Ajustes menores (resultado 8):** ok.

---

## E5: cómo armarlo

1. **Pre-registro de E5**, en un commit antes de correr:
   - las decisiones 1, 3 y 6;
   - la configuración de los equipos;
   - las métricas.
2. **Equipo A.** Se reconstruye con las reglas de E5, con la misma semilla y el mismo flujo de casos que E4. Si algún rol de A no llega al estado necesario para donar, se frena y se avisa. Los estados no se fijan a mano.
3. **Equipos B (con colaboración de A, rol por rol), B0 (control sin colaboración) y C (para cooperar con B en el mismo estado).** Se usan los mismos casos y semillas, y A9 en decisiones.
4. **Métricas por rol y por equipo:**
   - ciclos hasta cada cambio de estado;
   - teorías nuevas por capa;
   - %CEA;
   - fair(W);
   - celdas nunca resueltas;
   - compartidas aceptadas y rechazadas por Ω.
5. **Cálculo literal de L-3 entre configuraciones**, con las fórmulas de las Tablas L-16 y L-17. El neutro es el operador BIO. Las configuraciones son B0, B y la de cooperación.
6. **Figura** `p3_maduracion_equipos.png`. Si B no madura antes que B0, se reporta tal cual.

**Punto de control:** al terminar E5. Sin push.
