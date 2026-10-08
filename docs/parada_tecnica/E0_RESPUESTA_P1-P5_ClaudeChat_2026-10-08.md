# Respuesta a E0: decisiones P1–P5 y ajustes para E1–E2

**De:** Claude chat, con delegación de Kevin. **Fecha:** 08/10/2026.
**Para:** Claude Code, rama `eje1/bloque-e` (`6148a17`). Este archivo se commitea junto con el primer commit de E1.

## Qué verificó Claude chat antes de decidir

Se revisó sobre el PDF de Ierache (2010) y el repo:

- **Fig. 4.13 y su texto (pp. 93–94), registro de teorías:** coincide con E0.
- **§4.4.7.2 y Fig. 4.21 (pp. 105–107), planificador por ranking:**
  - ordena por U, después mayor P, después menor K;
  - toma la teoría cuya Si es igual a la situación actual;
  - el plan es de una sola teoría;
  - no hay umbral de utilidad.

  Coincide con E0.
- **Anexo L-3, Tablas L-16 y L-17 (pp. 267–270):** valores y fórmulas coinciden con E0.
  - SARp: CEA 90, RCE 58, TNA 11, RTN 27.
  - SARr: CEA 57, RCE 32, TNA 37, RTN 51.
- **La observación algebraica es correcta.** Con las definiciones de L-3:
  - %TNA ≤ %RTN equivale a promedio ≤ máximo;
  - %CEA ≥ %RCE equivale a máximo ≥ promedio.
- **`b267323` existe:** es un commit del 06/06/2026 y contiene `src/moav_hr/pipeline/dag.py`, con un `StateGraph` de los 5 agentes. Su docstring lo presenta como la versión «production-stack», junto a un Orchestrator liviano.

---

## P1 · Regla de evolución por agente

**No se aprueba como estaba propuesta; se adopta la variante de abajo.**

**El problema.** Medir %CEA como mejora respecto del primer intervalo de la propia capa:

- **Invierte el efecto que tiene que mostrar el punto 3.** Penaliza al agente que recibe colaboración, porque arranca alto y mejora poco, y premia al que arranca de cero.
- **No es lo que hace L-3.** En L-3 el «mínimo» es el SAR neutro (SN o SNr), no el arranque del propio SAR.

**La regla adoptada** es una adaptación declarada de la Fig. 4.28 y de L-3. Se evalúa para cada agente *a* al cierre de cada intervalo de n ciclos dentro de la capa:

1. **CE_a** = ciclos exitosos de *a* en el intervalo. Un ciclo es exitoso si termina con una teoría de u_tarea > 0,75 (p. 118); con α = 1 coincide con U.
2. **CE_0** = ciclos exitosos del **SAR neutro** del mismo rol sobre **los mismos casos** del intervalo. El SAR neutro usa solo el operador BIO, sin teorías ni compartición; es el contrafáctico determinista del simulador y equivale a SN o SNr de L-3. Su ciclo es exitoso si la acción fue la correcta.
3. **%CEA_a** = 100 · (CE_a − CE_0) / max(CE_0, 1). Condición: **%CEA_a ≥ %RCE**.
4. **%TN_a**, solo si *a* recibió colaboración en la capa: 100 · (teorías nuevas de *a* en el intervalo) / n. Las teorías recibidas por colaboración no cuentan como nuevas. Condición: **%TN_a ≤ %RTN**: pocas teorías nuevas significa una base representativa, en el sentido de las pp. 63 y 123–124.
5. **Promueve** si se cumplen (3), (4) cuando corresponde, y el **gate de Ω**:
   - puntual, con τ = 0,8 sobre las ventanas del agente;
   - el certificado se informa pero no se exige, porque con esta historia no puede aprobar (m_min = 47).

**Valores pre-registrados** en `configs/parada_tecnica.yaml`, en un commit propio **antes** de la primera corrida:

| Parámetro | Valor |
|---|---|
| n (ciclos por intervalo; también es la ventana de fair(W) del agente) | 20 |
| N_BIO, ciclos de la capa BIO | 60 |
| N_TBO, ciclos de la capa TBO | 100 |
| N_WIO, ciclos de la capa WIO | 100 |
| %RCE | 25 |
| %RTN | 20 |

- Cada valor lleva en el YAML una línea con su justificación.
- No se copian los valores de L-3 (58/27, 32/51): son de otra escala y de otra comparación.
- Si algo hay que cambiarlo, va en un commit nuevo con el motivo y se reporta en el informe.

**Fidelidad a L-3 en E5 (punto 3).** Reproducir el cálculo **exacto** de L-3 **entre configuraciones**, como lo hace Ierache:

- el mínimo es el neutro (operador BIO solo);
- la configuración evaluada es la del equipo con colaboración;
- el promedio es el de las configuraciones corridas: neutro, sin colaboración, con colaboración y con cooperación.

Reportar %CEA, %RCE, %TNA y %RTN con las fórmulas literales de las Tablas L-16 y L-17. Es el uso que la fuente les da.

**Redacción (obligatoria).** La observación algebraica va en tono neutro. No se usan las palabras «tautología» ni «error». Texto base:

> «En la tesis, los porcentajes se determinan comparando configuraciones de SAR (Anexo L-3, Tablas L-16 y L-17). Para decidir la promoción de un agente individual durante su actuación se operacionalizan como sigue: …»

La consecuencia algebraica va como **nota técnica para conversar con Jorge**, no como corrección. Lo mismo vale si en la Fig. 4.28 el sentido de la desigualdad de %TNA no coincide con el texto de las pp. 123–124: se reporta como una pregunta, nada más.

**Diseño del entorno, también pre-registrado.** Se fija y se documenta en `instances/hr/entorno.py` antes de correr, y no se ajusta después para que «dé»:

- **El operador BIO de cada rol tiene que ser imperfecto en algunas regiones de situaciones.** Si acierta todo, CE_0 = n y nadie puede superar al neutro.
- **El catálogo de situaciones tiene que ser acotado,** para que las teorías se reutilicen y la tasa de teorías nuevas pueda bajar.
- **Hay que documentar:**
  - la cantidad de celdas de Si y su frecuencia;
  - la precisión esperada del operador BIO por celda;
  - el ruido de WIO.

---

## P2 · Momento de la promoción

**Aprobado.**

- Se evalúa al cierre de cada intervalo y se promueve apenas se cumple la regla. El agente pasa al escenario de la capa siguiente desde el ciclo siguiente.
- Si se agotan los N ciclos de la capa sin cumplirla, el agente queda en su estado y la capa termina sin evolución (Fig. 4.28). No se repite la capa.
- Se declara que la p. 63 asocia los estados al fin de la capa y que la promoción anticipada viene de la Fig. 4.28.

---

## P3 · U por teoría

**Aprobado, con tres agregados.**

**Base.** u_tarea del Matcher ∈ {0, 1}: vale 1 si A es la acción correcta para el resultado observado en Sf. Con α = 1, U = u_tarea, constante por teoría.

**1. Validez del plan (adaptación declarada).** El planificador de Ierache sigue la primera teoría del orden (U, P, −K) cuya Si es igual a la actual, sin umbral (§4.4.7.2). Con U binaria, eso puede hacer repetir para siempre una acción que fracasó, si es la única teoría de la celda.

- **Regla:** la primera teoría del orden es plan válido **solo si su u_tarea > 0**, es decir, si permite «realizar una acción con sentido» (p. 106).
- **Si no hay plan válido, se recurre al «azar»** del planificador, el «plan por contingencia (azar)» del Alg. 4.5, y se cuenta como azar:
  - en los escenarios BIO y TBO (casos sintéticos de entrenamiento): la primera acción todavía no probada en esa celda, en un orden fijo; si ya se probaron todas, el operador BIO;
  - en WIO: el operador BIO.
- **Ninguna decisión aleatoria sobre personas** (DE-3).
- Cada aplicación de esta regla queda registrada en la traza.

**2. Fig. 4.21 frente al Alg. 4.7.** Contar y listar en la traza los casos en que el orden por P (Fig. 4.21, el que se usa) y el orden por P/K (Alg. 4.7) eligen teorías distintas. Es evidencia para la decisión 2 de la hoja.

**3. Cita de la p. 89.** Revisar la frase «U depende de (Si, A) (p. 89)». En la tesis, U es la utilidad de aplicar la acción en la situación para la tarea, y se calcula después de observar el resultado (pp. 61–62, región 4). Citar lo que dice el texto, sin parafrasear de más.

---

## P4 · Rescate de `dag.py`

**Autorizado.**

- Crear la rama **local** `rescate/langgraph-junio` en `b267323`. Sin push: la rama local ya lo protege del gc. El push lo autoriza Kevin.
- E1 usa ese `dag.py` como base, adaptado al `core/` actual, que no puede importar `instances/`.
- Registrar en `ESTADO.md` y en el informe, en tono neutro:

> «La orquestación con LangGraph existió desde la primera versión (06/06/2026, `pipeline/dag.py`) y quedó fuera del historial al reorganizarlo. El Bloque E la restituye como orquestador del DAG.»

---

## P5 · Modo llm (E8)

**Queda para después de E7.** No levantar Ollama ahora.

---

## Ajustes para E1–E2

1. **G11.** En el modo LLC, la acción del agente es la A de la teoría del plan (plan de longitud uno, §4.4.7.2). El empuje de ±0,03 queda solo en el modo heredado.
2. **G12.** En el motor nuevo, cada región lleva el número que le corresponde en el LLC: R1 a R7 según §4.2, pp. 62–63. En el modo heredado no se cambian las salidas existentes; la discrepancia se documenta en `ESTADO.md`.
3. **Registro de teorías** (Fig. 4.13, pp. 93–94):
   - teoría igual → P + 1, K + 1, y K + 1 en las similares;
   - teoría similar → P = 1, K = K_similar + 1, y K + 1 en las demás similares;
   - sin similares → P = 1, K = 1.

   Se usa la rama «sin mutación» de la Fig. 4.13; la mutación (§4.4.5) queda fuera de alcance y se declara. Un test verifica ΣP = K por celda después de registrar, de cooperar y de colaborar.
4. **Azares.** Cuando el Matcher usa el operador BIO ante una celda vacía, cuenta como azar.
5. **Pre-registro.** El YAML y las reglas del entorno van en un commit propio **antes** de la primera corrida de P1.
6. **Punto de control de E2.** Frenar con todo esto listo:
   - P1 y P2b corridos;
   - la traza región por región del ciclo 1;
   - la línea de tiempo de estados, con %CEA, %TN y el gate de Ω en cada intervalo;
   - las veces que se aplicó la regla de validez del plan;
   - los desacuerdos entre la Fig. 4.21 y el Alg. 4.7;
   - la sección «Resultados que no fueron los esperados».

---

## Preguntas para el encuentro con la dirección (no bloquean E1–E2)

- **Promoción de un agente individual.** La operacionalización de P1 y la nota técnica sobre L-3.
- **Validez del plan con U binaria** (P3).
- **Observación de Sf en producción.** Hoy el entorno de WIO siempre devuelve Sf. En un sistema real, a un candidato rechazado sin revisión no se le observa el resultado (son etiquetas selectivas). ¿Se modela en WIO? Por ahora no se implementa.
