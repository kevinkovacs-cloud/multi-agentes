# Respuesta al punto de control de E6: decisiones antes de E7

**De:** Claude chat, con delegación de Kevin · **Fecha:** 08/10/2026 · **Rama:** `eje1/bloque-e` (`bbe4bd2`)

Este archivo se commitea junto con el pre-registro corto de E6 v2.

## Criterio

- **E6 queda como está.** Es el resultado pre-registrado del punto 5.
- **Una sola revisión:** E6 v2 corrige cómo entra la equidad en la utilidad (decisión 1). Va con un pre-registro corto **antes** de correr. Se vuelve a correr solo lo que toca α = 0,5.
- **Todo lo demás es reporte, no cambia reglas.**

**Reconocimiento.** En E4_RESPUESTA escribí «paridad de errores (0,762 frente a 0,746)». Ese número es paridad de **aciertos**, no paridad de errores. El resultado 2 de E6 lo marca bien. El error fue mío.

---

## 1 · ê se calcula por celda (Si, A)

**Decisión: E6 v2.** ê se calcula **por celda (Si, A)**:

> ê(Si, A) = 1 − |tasa de error(AR) − tasa de error(no-AR)|, sobre E de todas las decisiones en las que se aplicó A en Si.

Con eso, U_rol(Si, A) = α·U(Si, A) + (1 − α)·ê(Si, A). Así la equidad puede cambiar la **acción**, que es lo que pide el punto 5: «las métricas de equidad que van a tener la función de utilidad de cada agente».

**Motivo.** En la v2 la U es de la acción (Si, A). Con ê por variante, α solo reordena variantes de la misma acción y no tiene ningún efecto sobre la decisión (resultado 1 de E6).

**Candidatas sin ê: el ajuste se aplica solo si todas las candidatas tienen ê.** Las candidatas que se comparan son la mejor variante de cada acción de la celda. Si alguna no tiene ê (menos de m_min lecturas en algún grupo), esa planificación usa α = 1 para **todas** y se registra «ajuste no aplicable: falta evidencia».

**Por qué así.** Con el respaldo actual, la candidata sin ê queda con α = 1 y la que tiene ê < 1 se penaliza: se **premia la falta de evidencia** (160 de 175 cambios). Imputar ê = 1 es lo mismo. Imputar un promedio sería arbitrario.

**Qué volver a correr**

- La corrida 1 con α = 0,5, sobre los mismos 600 casos.
- La condición programada con α = 0,5.

**Qué reportar**

- Cambios de **acción** y de teoría frente a α = 1.
- Aciertos y EO por grupo, porque el ajuste puede costar precisión y hay que mostrarlo.
- Cuántas planificaciones no pudieron ajustarse por falta de evidencia.
- La v1 y la v2, lado a lado.

**Advertencia para el documento de la dirección.** Dentro de una celda con acción fija, ê(Si, A) mide si la acción **se equivoca más con un grupo que con el otro**. Eso pasa cuando la Si no captura algo que se relaciona con el grupo. No mide trato desigual: ese se ve en la ventana.

---

## 2 · Métrica del Matcher: depende del nivel

| Nivel | Métrica | Por qué |
|---|---|---|
| Rol y ventana | **Odds igualadas: EO = max(\|ΔTPR\|, \|ΔFPR\|)** | Es lo que fijó la sección 6. Además ve lo que la paridad de aciertos esconde: en los casos de E4, aciertos 0,761 frente a 0,746, pero TPR 0,825 frente a 0,667. |
| Teoría o celda, ê(Si, A) | **Paridad de tasa de error** | Con la acción fija, TPR y FPR son triviales: todos los calificados de la celda reciben la misma acción. La tasa de error es lo único no trivial. |

**En `METRICAS_EQUIDAD_POR_ROL.md`** hay que nombrar cada cosa por su nombre y explicar por qué cambian con el nivel:

- **paridad demográfica:** sigue a la tasa base;
- **paridad de aciertos;**
- **odds igualadas:** TPR y FPR.

Hay que reemplazar «paridad de errores» por el término preciso en cada lugar. El texto base, con los números corridos: «Los tres criterios no coinciden y responden preguntas distintas.»

**Pregunta para el encuentro:** ¿qué criterio fija la dirección para el rol decisor? La propuesta es odds igualadas a nivel rol.

---

## 3 · Gate de compartición: queda como está, con dos cosas en el informe

**Decisión.** No se suma una auditoría por celda del rasgo proxy.

- **Exigiría saber de antemano cuál es el proxy.** En la condición programada lo sabemos; en general, no.
- **El gate aplica el estándar de evidencia acordado.** Con 300 decisiones por grupo, una brecha de 0,160 no se puede distinguir del azar con Hoeffding (cota de unos 0,17). Que no haya frenado es **correcto según ese estándar**.

**Para el informe y el encuentro**

1. **Límite.** El gate usa la brecha del resultado favorable, que a nivel rol es paridad demográfica. No separa la tasa base del sesgo: frena de más cuando las tasas base difieren y no ve un sesgo por debajo de lo detectable.

   **Propuesta para después de la parada técnica:** que el gate use la **métrica del rol** (odds igualadas para el Matcher). No se implementa ahora.
2. **Señal de alerta que ya existe.** El d_TV de la Si frente al grupo (B3) dio 0,767 en la condición detectable: la Si deja inferir el grupo. Hay que presentarlo como **alerta de proxy para revisión humana** del Monitor, no como gate. Es una propuesta, sin implementación.

**Pregunta para el encuentro:** ¿qué hacer con los sesgos por proxy que están por debajo del umbral detectable? Opciones:

- reportar el d_TV como alerta;
- exigir más historia antes de compartir;
- aceptar el límite.

---

## 4 · Control sin sesgo en la condición programada

**Decisión: sí, en E7, rotulado como «control agregado después de ver los resultados; no pre-registrado».**

**El control:** un Matcher que aprende sobre los mismos casos de la corrida 2, **sin** el rasgo `titulo_local` en la Si y con el operador BIO sin sesgo. Separa la tasa base (≈ 0,103) del sesgo residual que deja el operador sesgado (0,160 en paridad demográfica).

**Qué reportar:**

- paridad demográfica, odds igualadas y aciertos;
- la diferencia con el Matcher sesgado que aprende.

Es solo descriptivo: no cambia ninguna regla ni conclusión pre-registrada.

---

## E7: informe y cierre

1. **`generar_todo.py`** corre P1, P2a, P2b, P3, P4 y P5 (y E6 v2) y regenera los informes. Verificar que dé byte a byte lo commiteado.
2. **`INFORME_PARADA_TECNICA.md`** tiene una sección por punto del pedido (1, 2a, 2b, 3, 4 y 5), y cada sección incluye:
   - qué se demuestra;
   - el comando para reproducirlo;
   - los números clave;
   - las figuras;
   - los rótulos;
   - los resultados inesperados;
   - el historial de revisiones (v1 → v2, con su motivo).

   Al final, la **lista consolidada de preguntas para el encuentro**, sin duplicados:
   - decisión 1 de la hoja: evidencia de sesgo o evidencia de equidad;
   - A9 en decisiones o en ventanas;
   - Ω sin ciclo de vida;
   - con qué se compara un agente dentro de un equipo;
   - criterio del rol decisor;
   - sesgo por proxy por debajo de lo detectable;
   - ¿se modela la observación selectiva en WIO?;
   - Si, A y Sf por rol;
   - %RCE, %RTN, n y α;
   - semántica LLC de P y K (decisión 2);
   - similitud como extensión del planificador.
3. **`LEEME_REUNION.md`:** un guion de 10 líneas para mostrar en vivo, con comandos y archivos. Una traza HTML de P4, la figura de maduración de equipos y la de sesgo programado.
4. **`ESTADO.md`:** sección «Bloque E» con lo hecho, lo pendiente y lo que depende de la dirección.
5. **Lenguaje del informe:**
   - nunca «demuestra la conjetura» ni «valida»;
   - siempre «ilustrativo, entorno simulado»;
   - selección de personal = dominio de experimentación.
6. **Frenar en el punto de control de E7.** Claude chat revisa el informe antes de cualquier push.
