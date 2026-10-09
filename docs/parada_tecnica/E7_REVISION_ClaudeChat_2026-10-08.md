# Revisión del informe final (E7): correcciones antes del push

**De:** Claude chat · **Fecha:** 08/10/2026 · **Rama:** `eje1/bloque-e` (`f9fef26`)
**Revisado:** `INFORME_PARADA_TECNICA.md`, `LEEME_REUNION.md` y `METRICAS_EQUIDAD_POR_ROL.md`.

## Veredicto

El informe está bien armado y es honesto:

- tiene una sección por punto del pedido;
- cada número sale de una corrida reproducible;
- el historial de revisiones está a la vista, igual que los resultados inesperados;
- las preguntas están consolidadas.

`METRICAS_EQUIDAD_POR_ROL.md` usa la terminología correcta, y el límite del gate y la alerta de proxy figuran como propuestas, que es lo que corresponde.

Hay **seis correcciones de contenido**. Van en el generador (los documentos son «generados por código»), no a mano.

## Correcciones

1. **Punto 3: falta la nota técnica sobre L-3.** El informe muestra el cálculo literal de L-3 con «evoluciona», y en Parser y Explainer queda %TNA 100,0 ≤ %RTN 100,0. Leído solo, parece una validación. Agregar justo después de los números:
   - **La nota técnica,** igual que en `p3_equipos.md`, en tono neutro, para conversar con Jorge:
     - con estas definiciones, %TNA ≤ %RTN equivale a «promedio ≤ máximo»;
     - %CEA ≥ %RCE equivale a «configuración evaluada ≥ promedio».
   - **Qué significa 100 = 100:** B no generó teorías propias en Parser ni en Explainer porque las recibió todas de A. La condición se cumple por igualdad.
   - **Por qué el %CEA del Explainer es tan alto (602,7 %):** el operador BIO neutro casi nunca completa la explicación, así que CE_0 es muy bajo.
2. **Punto 3: cuánto pesa el diseño del entorno en las magnitudes.** Agregar: «Las magnitudes dependen del entorno pre-registrado: los operadores BIO son imperfectos por construcción, y el equipo neutro resuelve 21 de 260 casos. Los resultados muestran el mecanismo de colaboración y maduración, no cuánto ayudaría en un sistema real.»
3. **Punto 4: el Bias Auditor.** Donde dice «Bias Auditor Born», poner: «Bias Auditor: Born en E4; desde E5 no tiene estados por diseño (su regla es regulatoria; decisión 1 de E4_RESPUESTA)».
4. **Punto 5: qué significa que α = 0,5 no haya cambiado nada.** Agregar tres cosas:
   - **El test que muestra que el ajuste funciona.** Nombrarlo (archivo y nombre del test): con evidencia en las dos acciones y U parecidas, α = 0,5 cambia la acción.
   - **La causa estructural,** que ya está en `METRICAS_EQUIDAD_POR_ROL.md` y tiene que estar también en el informe, en una frase completa: «El ajuste por equidad necesita evidencia sobre la acción que el agente no elige, y el aprendizaje deja de generarla (en 1354 de 1758 planificaciones faltó evidencia). Es una propiedad del tamaño de muestra y de la explotación, no de la definición.»
   - **El control post hoc:** la diferencia entre el Matcher sesgado que aprende (0,160) y el control (0,080) da una idea del sesgo residual atribuible al proxy, del orden de 0,08. Siempre con la salvedad de que el control no es un contrafáctico limpio.
5. **Sección «Estado»: la infraestructura.** Agregar la frase de `ESTADO.md` sobre LangGraph: «La orquestación con LangGraph existió desde la primera versión (06/06/2026) y quedó fuera del historial al reorganizarlo; E1 la restituye (`core/grafo.py`); el código de junio queda en la rama local `rescate/langgraph-junio`.»
6. **Pregunta 12 para el encuentro, nueva:** «Equidad en la utilidad con poca evidencia. Con m_min = 5 lecturas por grupo, el ajuste casi nunca se aplica, porque el agente deja de probar la acción que no elige. ¿Se exige exploración mínima para estimar la equidad de ambas acciones, se baja m_min o se acepta el límite?»

## Cierre técnico

7. **Commitear el handoff que está sin seguimiento en la raíz,** `HANDOFF_CLAUDE_CODE_bloqueE_parada_tecnica_2026-10-08.md`, junto con este archivo de revisión.
8. **Regenerar y verificar:** `generar_todo.py --verificar` (todo idéntico, salvo los documentos corregidos) y `pytest`. Confirmar que las salidas viejas no cambian.
9. **Push:** solo si Kevin lo autoriza en el mensaje con que te pase este archivo. Se suben las ramas `eje1/bloque-e` y `rescate/langgraph-junio` a origin. **No** se hace merge a `main`: `main` queda congelada hasta después del encuentro con la dirección.
