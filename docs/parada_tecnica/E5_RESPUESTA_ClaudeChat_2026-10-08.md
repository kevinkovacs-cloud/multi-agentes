# Respuesta al punto de control de E5: decisiones antes de E6

**De:** Claude chat, con delegación de Kevin · **Fecha:** 08/10/2026 · **Rama:** `eje1/bloque-e` (`3e571e0`)

Este archivo se commitea junto con el pre-registro de E6.

**Criterio general:** E5 queda como está. Las dos métricas nuevas (1 y 2) son **descriptivas**: se calculan sobre las corridas ya hechas y no cambian ninguna regla ni ninguna promoción. Se agregan al informe de E5 en un commit propio, sin volver a correr los equipos.

---

## 1 · Punto de comparación de %CEA dentro del equipo

**Decisión:** las dos cosas, cada una con su función.

- **Para la promoción (región 7):** se mantiene el contrafáctico sobre las **propias entradas** del rol, como está pre-registrado. Es lo correcto para la evolución de un agente, porque aísla lo que aprendió **ese** agente. Si se lo comparara contra el equipo neutro N, al Matcher se le acreditaría lo que aprendió el Parser.
- **Para comparar equipos (punto 3 del pedido):** se agrega el desempeño de cada rol y del equipo contra el **equipo neutro N**: aciertos del rol con las entradas que le dio su propio equipo, frente a los del rol neutro con las entradas del equipo neutro. Es una métrica descriptiva de nivel equipo.

**Lo que hay que contar en el informe** (resultado 1 de E5). La promoción del Matcher de B fue más lenta que la de B0 porque su vara era más alta: su Parser ya extraía bien desde el caso 1, y el SAR neutro sobre esas entradas también acertaba más. Aun así:

- el equipo B acertó más que B0 (204 frente a 173);
- solo el Matcher de B llegó a Mature.

Texto base:

> «La regla de evolución mide lo que aprende cada agente, no el resultado del equipo; cuando un rol de arriba mejora, el de abajo tiene que superar una referencia más exigente.»

**Pregunta para el encuentro:** ¿la evolución de un agente dentro de un equipo se mide contra sus propias entradas (lo que aprendió él) o contra el equipo neutro (su aporte al resultado conjunto)?

---

## 2 · Efecto techo de la promoción por intervalos

**Decisión:** la regla no cambia. Se agregan **curvas de aprendizaje sin piso**, que son las propias estadísticas del LLC (§4.4.9 y región 7):

- **Por rol y por ciclo, B frente a B0 (y C):**
  - ciclos exitosos acumulados;
  - teorías nuevas acumuladas.
- **Por rol:** el **primer ciclo en que se cumpliría la regla** si se evaluara en cada ciclo y no solo en los cierres. Es descriptivo; la promoción real sigue siendo al cierre del intervalo.

**Figura:** `p3_curvas_aprendizaje.png`, un panel por rol. Si la colaboración no adelanta a Parser y Explainer ni con estas métricas, se reporta tal cual.

**Texto base para el informe:**

> «Con intervalos de 20 ciclos, la promoción tiene un piso de 20 ciclos por estado; para Parser y Explainer ese piso domina y la colaboración no puede adelantarla. Las curvas muestran el efecto que el piso oculta.»

---

## 3 · El Matcher de C no coopera

**Decisión:** se informa tal cual. **No** se cambia la semilla de C.

- **Es el axioma funcionando:** solo cooperan SAR en el mismo estado (§4.3.1 [a], p. 70). El Matcher de C no superó al neutro en BIO (%CEA −9,1, 0,0 y 5,1), siguió en Born y no puede cooperar con un Novice.
- **La cooperación entre Matchers ya está demostrada:** en P2a (E3, con A9 en decisiones) la cooperación B ↔ C del Matcher se aceptó.
- **Para el informe:** en E5, la cooperación de equipo se ve en Parser y Explainer.

---

## 4 · E6: sí, con la condición de sesgo programado

Hay que pre-registrar, **antes de correr**, lo siguiente.

### Métricas de equidad por rol

Según la sección 6 del handoff:

| Rol | Métrica de equidad |
|---|---|
| Parser | Brecha de completitud entre grupos (y d_TV del canal proxy como métrica de auditoría). |
| Matcher | Paridad de errores (equalized odds) en la ventana, y ê(t) por teoría desde E(t). |
| Bias Auditor | Paridad de derivación (Δ_esc). |
| Explainer | Brecha de completitud de la explicación. |

Para cada rol, el documento `METRICAS_EQUIDAD_POR_ROL.md` tiene que incluir:

- la definición y la fórmula;
- el plano del que sale cada dato (decisión o auditoría);
- `m_min`;
- los límites, incluida la advertencia formal de la sección 6.

### U_rol con α = 1 y α = 0,5, lado a lado

- La duración de la corrida se pre-registra de modo que **algunas** teorías lleguen a `m_min` = 5 usos por grupo. Se informa cuántas llegan.
- Si α = 0,5 no cambia ninguna elección, se reporta.

### Paridad demográfica frente a paridad de errores

El resultado 5 de E4 se usa como ejemplo corrido: la brecha de paridad demográfica de 0,154 sale de las tasas base, con paridad de errores pareja (0,762 frente a 0,746). Es la razón para medir al Matcher por paridad de errores.

### Condición con sesgo programado

Lleva el rótulo «parámetros programados», como en D5.

- **El sesgo entra por un proxy, no por el atributo protegido.** Así se respeta DE-4: el atributo sigue fuera de Si, A y los prompts. Un operador BIO del Matcher penaliza un rasgo de la Si que correlaciona con el grupo; si el entorno no tiene ese rasgo, se lo agrega y se lo declara. Es el caso realista: discriminación indirecta.
- **Dos magnitudes, fijadas antes de correr con la característica operativa (E2 v2):**
  1. una **detectable** con la evidencia acumulada en la capa, dentro de la duración de la corrida;
  2. una **por debajo del umbral de detección**, para mostrar el límite.
- **Para cada magnitud:**
  - (i) la regla del Auditor con ventana de 20;
  - (ii) la regla con evidencia acumulada en la capa, con δ/L, que deriva la ventana en curso;
  - (iii) qué pasa con el gate de evolución y con la compartición del Matcher sesgado;
  - (iv) si el aprendizaje desde los resultados atenúa el sesgo del operador BIO a medida que las teorías reemplazan al operador.
- **Rótulo obligatorio para (iv):** «ilustra el mecanismo; no es evidencia de la conjetura de atenuación».

### Lo que no cambia

Todo lo demás de E5.

**Punto de control:** al terminar E6. Sin push.
