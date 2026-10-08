# E0 · Diagnóstico de la prueba de concepto frente al LLC de Ierache (2010)

**Bloque E — «Parada técnica».** Fase E0: diagnóstico, **sin cambios de código**.
**Fecha:** 08/10/2026 · **Rama:** `eje1/bloque-e`, creada desde `eje1/formalizacion-v2` en `58ce027`.

> Rótulos del bloque: *ilustrativo, entorno simulado (modo sim); no es evidencia experimental* · *semántica LLC
> propuesta; decisiones 2, 4 y 5 pendientes de la dirección*. E0 no corre demos: los únicos números propios de
> este documento son el resultado de `pytest`; el resto son transcripciones de la fuente, con su página.

**Fuente.** Ierache, J. S. (2010). *Modelo de ciclo de vida para el aprendizaje basado en compartición de
conocimientos en sistemas autónomos de robots* (tesis doctoral, UNLP). Copia local:
`academico/doctorado/Bibliografia para leer/01 · LLC de Ierache y trabajos del grupo/Ierache_2010_Tesis-doctoral-LLC__leer_pp59-63_105-116_120_233.pdf`.
**Paginación:** en todos los tramos citados acá (pp. 59–128 y 249–270) la página del PDF coincide con la
impresa al pie; se cita siempre la impresa. Las figuras 4.28 y las tablas L-16/L-17 se leyeron sobre la
imagen de la página, porque la capa de texto pierde los símbolos de comparación.

---

## 0. Resumen

- **Base verificada:** `58ce027`, árbol limpio, `pytest -q` → **146 passed, 1 skipped** (el omitido es el
  test «sin el extra de embeddings», porque el `.venv` tiene `sentence-transformers` desde el Bloque D).
- **G1–G10:** se confirman **ocho** (G1, G2, G4, G6, G7, G8, G9, G10) y **dos parcialmente** (G3 y G5): el
  matiz de cada uno está en la sección 2.
- **Dos hallazgos nuevos:**
  - **G11.** La teoría elegida no decide la acción: en modo sim solo corre el puntaje ±0,03·confiabilidad.
    En el LLC, la acción de la teoría elegida *es* el plan.
  - **G12.** Hay regiones del registro de auditoría mal rotuladas: el Explainer registra «región 6» y la
    decisión final del Orchestrator, «región 7».
- **LangGraph (G9):** hubo una orquestación con LangGraph. El fuente `pipeline/dag.py` (un `StateGraph` de los
  5 agentes) se perdió al colapsar el historial y sobrevive solo en el reflog, en el commit `b267323` (06/06),
  blob `e585c35`. Conviene protegerlo antes de E1 (sección 5).
- **Regla de evolución:** transcriptas las fórmulas de %CEA, %TNA, %RCE y %RTN (Fig. 4.28, p. 123) y los
  valores del Anexo L-3 (pp. 267–270).
  - Con las cantidades de L-3, la condición %TNA ≤ %RTN se cumple siempre y %CEA ≥ %RCE equivale a «la
    configuración evaluada supera el promedio» (sección 1.8).
  - Los umbrales no se pueden trasladar tal cual a un agente individual: hay que definirlos antes de E2
    (DE-9; pregunta P1 de la sección 4).
- **Lo que ya existe y sirve para E2:**
  - `TheoryBase.select` (`core/theory.py:195-209`) ya implementa el planificador ranking del LLC: misma celda
    de Si y orden de la Fig. 4.21. Pero **nadie la llama**.
  - Ante una celda vacía, el Matcher usa su regla base (`semantic_matcher.py:28-29`): es la «regla del
    diseñador» de DE-3, que hoy no se cuenta como «azar».

---

## 1. Transcripción de la fuente

### 1.1 La teoría y los parámetros P y K — §4.1.2 (pp. 60–61) y §4.4.4 (pp. 92–94, Fig. 4.13)

- **Tupla:** la teoría es la tupla ⟨Si, A, Sf, P, K, U⟩ (p. 60).
  - Si es el estado al querer ejecutar la acción y Sf el estado después de ejecutarla; Sf tiene la misma
    estructura que Si.
  - **P** es la «cantidad de veces que teniendo la situación inicial (Si), se ejecutó la acción (A) y se obtuvo
    la situación final (Sf)».
  - **K** es la «cantidad de veces que teniendo la situación inicial (Si), se ejecutó la acción A» (p. 60).
- **Al confirmarse una teoría,** «su P y K aumentan, aumentando también el K de las teorías complementarias
  (teorías con las mismas condiciones supuestas y las mismas acciones)» (p. 60). P/K es la confiabilidad (p. 61).
- **Formación:** la teoría se formula *después* de registrar la situación siguiente a la acción (p. 61).
- **Registro** (Fig. 4.13, p. 93; texto, pp. 93–94):
  - **Teoría igual** (misma Si, A y Sf): P + 1, K + 1, y K + 1 en cada teoría **similar**.
  - **Teoría similar** (misma Si y A, otra Sf): la nueva entra con **P = 1, K = K_similar + 1**, y cada
    similar recibe K + 1.
  - **Sin similares:** entra con **P = 1, K = 1**.
  - Opcional: mutación de teorías (§4.4.5). Queda fuera de alcance del Bloque E.
- **Invariante:** «luego de la colaboración la suma de los P de las teorías similares en el SAR receptor es
  igual al K de cualquiera de ellas» (§4.4.8.2, p. 113).

### 1.2 Siete regiones, capas, estados y escenarios — §4.2 (pp. 61–64)

- **Componentes:** siete regiones, tres capas (BIO, TBO, WIO) y cuatro estados (born, newbie, trained,
  mature) «asociados al principio y fin de cada una de las layers» (p. 62). En cada capa, el SAR transita cada
  región «durante una cantidad determinada de ciclos percepción-acción» (p. 62).
- **Escenarios:**
  - BIO-escenario: Born → Newbie.
  - TBO-escenario: Newbie → Trained.
  - WIO-escenario: Trained → Mature (p. 62).
  - Cada uno tiene complejidad creciente (§4.5, pp. 124–126).
- **Regiones:**
  - **R1.** Sensado y normalización de la situación inicial (p. 62).
  - **R2.** Ejecución de la acción (p. 62).
  - **R3.** Situación final, sensada después de la acción (p. 62).
  - **R4.** Cálculo de utilidad (p. 62).
  - **R5.** Ponderación de P y K y registro de la teoría (p. 63).
  - **R6.** Estadísticas: situaciones, teorías nuevas, acumuladas y exitosas, ciclos exitosos, planes,
    teorías por intervalo de U y azares (p. 63).
  - **R7.** Evolución: ciclos exitosos (tienden a crecer), teorías nuevas propias (tienden a decrecer),
    teorías vs. situaciones, planes exitosos y teorías exitosas con 0,75 < U ≤ 1. Son **métricas primarias**
    los ciclos exitosos y las teorías nuevas; estas últimas, solo «en el caso de que el SAR reciba
    colaboración» (p. 63).
- **Estados por capa** (p. 63):
  - Born al inicio de BIO;
  - Newbie al finalizar BIO;
  - Trained al finalizar TBO;
  - Mature al finalizar WIO.
- **Configuración por capa** (p. 64; §4.4.2.1, pp. 83–85):
  - ambiente según la capa;
  - cantidad de ciclos;
  - método de comparación;
  - base de conocimiento según el estado;
  - estadísticas, con su intervalo de muestra;
  - %RCE y %RTN «a alcanzar para la evolución de estado» (Fig. 4.9).

### 1.3 Axiomas de compartición — §4.3.1 (pp. 69–70) y algoritmos

- **Axioma [a]:** la cooperación se da solo entre SARs del mismo estado de evolución.
- **Axioma [b]:** la colaboración va de un estado superior a un receptor de estado inferior.
- **Axiomas [c]–[f]:** detallan los casos posibles por estado (p. 70).
- **Algoritmos:**
  - Alg. 4.9, cooperación (p. 109): la base común queda para los dos SARs.
  - Alg. 4.10, colaboración (p. 116): la base queda solo para el receptor.
  - Verificación de estados (p. 113, Fig. 4.26, p. 117).

### 1.4 Utilidad U — §4.4.3 (pp. 87–92)

- **Métodos:** hay dos. El aplicado es el **basado en la acción** (p. 87): compara la velocidad de la
  acción de la teoría con la que daría el robot reactivo de Braitenberg para esa situación, y normaliza a
  [−1, 1] (pp. 89–90, Alg. 4.2).
- **Lo que dice el texto** (revisado el 08/10, punto 3 de P3): «El parámetro U, utilidad (U), indica la
  utilidad de la teoría en función de la tarea asociada al SAR. Se calcula con una fórmula, que indica si
  los resultados de la teoría fueron o no fructíferos para el robot» (p. 61). Se calcula en la región 4,
  después de la situación final (p. 62). En el método aplicado, la fórmula compara la velocidad de la
  acción de la teoría con la que daría el robot reactivo en esa situación (pp. 89–90).
- **Teoría exitosa:** 0,75 < U ≤ 1 (p. 63; p. 89; p. 120).
- **SAR born reactivo:** se mueve con la regla de su creador «sin necesidad de adquirir más conocimientos»
  (p. 91). El SAR reactivo «se emplea para generar una base de conocimiento de teorías iniciales» (p. 84).

### 1.5 Comparación de situaciones — §4.4.6 (pp. 97–100)

- **Tres métodos:**
  - **[a] exacto;**
  - **[b] umbral común y fijo,** que discretiza cada sensor a 0/1 con umbral 750;
  - **[c] umbral individual por sensor y por rueda,** con el desvío estándar de 600 ciclos de un SAR born
    reactivo. Es el que usa la tesis (pp. 97–99).
- **Igualdad:** dos situaciones son iguales si ninguna diferencia por sensor supera su umbral (pp. 99–100).

### 1.6 Planificador ranking y «azar» — §4.4.7 (pp. 100–108)

- **Orden de la Fig. 4.21** (p. 107): primero **U desc**, después **P desc** y por último **K asc**.
- **Aplicabilidad:** entre las teorías así ordenadas, la primera cuya Si coincide con la situación actual,
  según el método de §4.4.6 (p. 106).
- **El plan es una sola teoría:** su acción se ejecuta en el ciclo siguiente (pp. 106–107).
- **Alg. 4.7** (p. 108) desempata «por P/K», que no es lo mismo que la Fig. 4.21. La diferencia ya está
  planteada en la hoja, en la decisión 2.
- **«Azar»** (Fig. 4.17, p. 101; p. 102; p. 83; p. 118):
  - si no hay un plan viable, «se obtiene una teoría de la base de conocimientos a través de una selección
    al azar y se actualiza el contador de azares»;
  - la estadística cuenta «la cantidad de planes que recurren a acciones al azar»;
  - al principio, el SAR «selecciona una acción al azar» (p. 59).

### 1.7 Estadísticas de la región 6 — §4.4.9 (pp. 117–122, Fig. 4.27)

- **Qué se registra:** por intervalo de n ciclos (p. 117):
  - situaciones;
  - teorías acumuladas;
  - teorías por intervalo de U ([0–0,25], [0,25–0,5], [0,5–0,75] y [0,75–1]);
  - planes, planes exitosos y sin éxito;
  - azares;
  - P/K por intervalo y P/K general;
  - ciclos exitosos (p. 118).
- **Ciclo exitoso:** el que «finaliza con una teoría cuya utilidad (U), resulta mayor a 0.75» (p. 118).
  El ejemplo de la Tabla 4.2 (p. 119) usa «≥ 0,75»; se adopta la definición del texto (> 0,75).
- **Teorías exitosas:** las acumuladas más las generadas en la actuación con U > 0,75 (p. 118).
- **Teorías nuevas:** la diferencia de teorías acumuladas entre el intervalo n + 1 y el intervalo n (p. 121).

### 1.8 Evolución de la región 7 — §4.4.10 (pp. 122–124, Fig. 4.28) y Anexo L-3 (pp. 267–270)

**Fórmulas** (Fig. 4.28, p. 123, leídas sobre la imagen):

- %CEA = (Máx. cantidad de ciclos exitosos alcanzados − Mín. cantidad de ciclos exitosos iniciales) / Mín.
  cantidad de ciclos exitosos iniciales.
- %TNA = (Cantidad promedio de teorías nuevas − Cantidad de teorías nuevas por colaboración alcanzadas) /
  Cantidad promedio de teorías nuevas.
- %RCE, «se determina en la configuración del SAR sobre la base de experimentos realizados» = ((Promedio
  cantidad de ciclos exitosos − Mínima cantidad de ciclos exitosos) / Mínima cantidad de ciclos exitosos) · 100.
- %RTN = ((Máx. cantidad de teorías nuevas − Cantidad de teorías de colaboración) / Máx. cantidad de teorías
  nuevas) · 100.

**Flujo** (Fig. 4.28):

1. Calcular %TNA y %CEA.
2. Si **%TNA ≤ %RTN** y **%CEA ≥ %RCE**, el SAR **evoluciona de estado**.
3. Si no y el ciclo actual ≤ cantidad de ciclos, el SAR «continúa N ciclos en el layer» y se vuelve a
   calcular.
4. Si se agotaron los ciclos, termina **sin** evolucionar.

La figura corresponde a «un SAR que recibió colaboración» (p. 123). Sin colaboración, la métrica es solo la
de ciclos exitosos (p. 63; p. 83 [h]; p. 122). En el texto (p. 124), si no se cumplen las condiciones, el
SAR «continúa en su layer de actuación, durante n ciclos, hasta alcanzar la cantidad de ciclos […] o cumplir
con las condiciones de evolución».

**Valores del Anexo L-3** (promedios de 10 corridas de 600 ciclos por configuración):

| Planificador | Datos | %CEA | %RCE | %TNA | %RTN | Tabla |
|---|---|---|---|---|---|---|
| SARp (clásico) | ciclos exitosos: mín. SN = 130, máx. SC = 248, prom. = 206 · teorías nuevas: máx. SN = 514, SC = 376, prom. = 423 | **90 %** | **58 %** | **11 %** | **27 %** | L-16 (pp. 268–269) |
| SARr (ranking) | ciclos exitosos: mín. SNr = 310, máx. SCr = 487, prom. = 409 · teorías nuevas: máx. SNr = 190, SCr = 93, prom. = 149 | **57 %** | **32 %** | **37 %** | **51 %** | L-17 (pp. 269–270) |

Ambas tablas cierran con «Evolución: CEA > RCE, TNA < RTN».

**Observación algebraica** (de este diagnóstico; para validar con Jorge, no es una corrección a la fuente).
En L-3, las cuatro cantidades se calculan **entre configuraciones**: el mínimo es el SAR neutro, el máximo y
la colaboración son el SAR con colaboración, y el promedio es el de los métodos. Con esas definiciones:

- **%TNA ≤ %RTN se cumple siempre.** Llamando c a la cantidad de teorías nuevas de la configuración evaluada,
  (prom − c)/prom ≤ (máx − c)/máx equivale a prom ≤ máx, que vale para cualquier conjunto de datos con c > 0.
- **%CEA ≥ %RCE** equivale a «los ciclos exitosos de la configuración evaluada ≥ el promedio de las
  configuraciones». En L-3 se cumple porque la configuración evaluada es la del máximo.

Consecuencia para el Bloque E: los porcentajes 58/27 (SARp) y 32/51 (SARr) son **umbrales de comparación
entre configuraciones** de la tesis, no umbrales que un agente individual pueda evaluar ciclo a ciclo. Para
aplicar la Fig. 4.28 a cada agente hay que definir las cantidades a nivel de agente y fijarlas en `configs/`
**antes** de correr (DE-9). Se propone cómo en la pregunta P1 (sección 4). El planificador del Bloque E es el
ranking; si se adoptaran valores de la tesis, los pertinentes son los de SARr (32 % y 51 %).

---

## 2. G1–G10 frente al código (`58ce027`), y dos hallazgos nuevos

| # | Veredicto | Evidencia (archivo:línea) | Matiz |
|---|---|---|---|
| **G1** El pipeline no ejecuta el ciclo | **Confirmado** | Cada `run()` registra una sola región: Parser R1 (`parser_agent.py:146`), Matcher R2 (`semantic_matcher.py:65`), Bias Auditor R4 (`bias_auditor.py:52`, `bias_auditor_exp.py:77`), Explainer «R6» (`explainability_agent.py:28`), Orchestrator R1 y «R7» (`orchestrator.py:36,47`). `learn` se llama solo en `pipeline.py:81` (warmup) y en `experiments/demos_direccion/comun.py:197`. Ningún evento de R3 ni de R5 en `src/`. | Solo el Matcher tiene teorías. Parser, Auditor y Explainer nunca llaman a `learn`. |
| **G2** Estado fijado en el constructor | **Confirmado** | Parser: `training_runs=5` + WIO bootstrap → Mature (`parser_agent.py:131-132`). Matcher: `training_runs=4` → Trained (`semantic_matcher.py:23`). Bias Auditor demo: `training_runs=6` + bootstrap → Mature (`bias_auditor.py:22-23`). Auditor experimental: `training_runs=6` → Trained (`bias_auditor_exp.py:60`). Explainer: `training_runs=1` → Novice (`explainability_agent.py:10`). El estado se deriva de contadores (`agent.py:58-65`). | No hay escenarios por capa ni ciclos por capa. `advance()` (D4a, `agent.py:136`) mueve contadores si Ω aprueba, pero no recorre escenarios. |
| **G3** Capa activa mal mapeada | **Parcial** | `lifecycle.py:41-46`: Born→BIO, Novice→TBO, Trained→TBO, Mature→WIO. | Born→BIO y Novice→TBO coinciden con p. 62. El desvío es **Trained→TBO**: en el LLC, Trained transita **WIO**. Mature ya terminó WIO, así que el mapa no está definido para él en la fuente. `_CUMULATIVE` («capas completadas») coincide con la fuente. |
| **G4** Regla de evolución distinta | **Confirmado** | `monitor.py:97-124`: el puntual compara reputación ≥ τ (l. 112-113) y el certificado usa la LCB de Hoeffding (l. 124). `agent.py:136-169` ejecuta el paso solo con ese gate. | Faltan %CEA y %TNA (Fig. 4.28) y la continuidad «N ciclos en el layer». Ver la observación de la sección 1.8 antes de implementarla. |
| **G5** Semántica de P y K distinta | **Parcial** | `theory.py:106-110` (`reinforce`: K + 1 y P + 1 si hubo éxito); `agent.py:89-101` (`learn`: igual → refuerza; nueva → P ∈ {0, 1}, K = 1); U = `(P+1)/(k_own+2)` si no se pasa `u` (`theory.py:104`, `agent.py:96,99`). | La identidad ya es (Q(Si), A, Q(Sf)), así que la estructura admite variantes. Pero `learn` (i) no suma K a las complementarias, (ii) da K = 1 a la variante nueva en vez de K_celda + 1 y (iii) cuenta en P el «éxito» y no «se obtuvo Sf». Por eso no se sostiene ΣP = K, y SHACL solo controla P ≤ K (`shapes.py:19-20`). Sobre D3 (0 similares): con la convención Sf = resultado observado, la causa fue de **datos**, no de semántica; en el warmup (Sf = acción) tampoco puede haber similares. |
| **G6** Base sembrada con la etiqueta | **Confirmado** | `pipeline.py:74-82`: siembra con los mismos candidatos y la acción derivada de `true_qual` (l. 79), con `success=True, u=0.9` (l. 81). La usan `run_poc.py:62` y `demo_caso.py:37`. | En D1, la base contiene la propia Si de Fátima: la consulta se encuentra a sí misma. |
| **G7** El planificador no restringe a la misma Si | **Confirmado** | `retrieval.py:75-83`: filtra por similitud ≥ δ (l. 76-77) y ordena por (−U, −P, K, −recencia, id) (l. 81) sobre **toda** la base. | Ya existe `TheoryBase.select` (`theory.py:195-209`): misma celda Q(Si) (`applicable`, l. 191-193) y orden de la Fig. 4.21 (l. 208). No la usa nadie (`grep '\.select('` → 0). Es la base natural de `core/planificador.py`. |
| **G8** Sin estadísticas de R6 | **Confirmado** | No hay contadores de ciclos exitosos, teorías nuevas, azares ni intervalos de U o P/K en `src/`. `Region.STATISTICS` existe (`lifecycle.py:36`), pero ningún evento la usa con ese sentido. | El único evento con `region=6` es la explicación (G12). |
| **G9** LangGraph | **Confirmado** | `git grep -i langgraph <rama> -- src` → 0 archivos en las 5 ramas locales y en sus remotos. `core/orchestrator.py:30-48` es un bucle secuencial. Lo único de LangChain es `langchain_ollama`, con import perezoso (`core/llm.py:25`). `langgraph==1.2.4` está en `requirements.lock.txt` e instalado, pero no se usa. | El `.pyc` huérfano (`src/moav_hr/pipeline/__pycache__/dag.cpython-312.pyc`, 06/06, ignorado por git) es la versión compilada de un `dag.py` con `StateGraph`. Su fuente sigue recuperable: commit `b267323` (reflog), blob `e585c35`, 86 líneas, nodos parser→matcher→auditor→explainer→orchestrator. El artículo (§5, `paper.tex:313`) y el README (l. 70, 130, 166, 169) dicen «sobre LangGraph». |
| **G10** Auditor con etiqueta y oráculo | **Confirmado** | `bias_auditor.py:30-33`: usa `bias_risk` del generador y ajusta a `true_qual` si bloquea; está declarado en su docstring (l. 7-11). El experimental sin oráculo está en `bias_auditor_exp.py`. | — |
| **G11 (nuevo)** La teoría no decide la acción | **Hallazgo** | `semantic_matcher.py:18,26-33`: en sim, score = base + 0,03 · confiabilidad · (±1) según la acción de la primera recuperada. En llm, las teorías van como few-shot (l. 40). | En el LLC, la acción de la teoría elegida **es** el plan (§4.4.7.2, pp. 106–107). Para el punto 2b del pedido, el planificador tiene que devolver la acción y no un ajuste del puntaje. |
| **G12 (nuevo)** Regiones mal rotuladas en el registro | **Hallazgo** | `explainability_agent.py:28` registra la explicación como `region=6`, con capa «WIO» en un agente Novice. `orchestrator.py:47` registra la decisión final como `region=7`. | En el LLC, R6 = estadísticas y R7 = evolución (p. 63). Una traza región por región (punto 4) heredaría estos rótulos. |

---

## 3. Mapa concepto del LLC → fuente → código actual → brecha → ítem del Bloque E

| Concepto del LLC | Fuente (sección · página impresa) | Código actual (`58ce027`) | Brecha | Ítem |
|---|---|---|---|---|
| Tupla ⟨Si, A, Sf, P, K, U⟩ | §4.1.2 · p. 60 | `core/theory.py:70-115` (`Theory`) | Ninguna en la estructura. | — |
| P y K (igual / similar / nueva) | §4.1.2 · p. 60; §4.4.4 · pp. 93–94, Fig. 4.13 | `agent.py:89-101`, `theory.py:106-110` | Sin K de las complementarias; la variante nueva no arranca con K = K_celda + 1; P = éxito (G5). | E2.1 (`learn_llc`, DE-1) |
| Invariante ΣP = K | §4.4.8.2 · p. 113 | `shapes.py:19-20` (solo P ≤ K); `sharing.py:45-105` | Falta en `learn` y en SHACL (I4). `_merge` ya suma el K de la celda. | E2.1 + E4 (shape) |
| Utilidad U por teoría | §4.4.3 · pp. 87–92 (U ∈ [−1, 1], según la acción) | U = Laplace o `u=0.9` del warmup (`agent.py:96,99`; `pipeline.py:81`) | U no es utilidad de tarea (decisión 2) ni tiene equidad (decisión 5). | E2 (u_tarea) + E6 (DE-5) |
| Teoría exitosa (0,75 < U ≤ 1) | §4.2 · p. 63; §4.4.9 · p. 120 | — | No se cuenta. | E2.4 |
| R1 · situación inicial | §4.2 · p. 62 | `parser_agent.py:134-148` (`build_si`) | La Si del Matcher la construye el Parser. Falta una interfaz `percibir` por rol. | E2.3 |
| R2 · acción con el planificador | §4.2 · p. 62; §4.4.7.2 · pp. 105–108, Fig. 4.21 | `retrieval.py:75-83` + empujón (G7, G11) | Similitud global en vez de la celda; la teoría no es el plan. | E2.2 (`planificador.py`, DE-2) |
| «Azar» cuando no hay plan | Fig. 4.17 · p. 101; p. 102; p. 118 | `semantic_matcher.py:28-29` (puntaje base, sin contar) | No se registra ni se cuenta. La regla del diseñador ya existe y coincide con el SAR reactivo (p. 84, p. 91). | E2.2 + E2.4 (DE-3) |
| Comparación de situaciones | §4.4.6 · pp. 97–100 | `q_canonical` sobre la Si discretizada (`theory.py:38-44`; `parser_agent.py:110-120`) | Equivale al método por umbral común (discretización). La similitud continua (coseno o embeddings) no está en la fuente. | E2.2 (extensión declarada) |
| R3 · situación final después de la acción | §4.2 · p. 62; §4.1.1 · p. 59 | — en `src/` (solo `comun.py` en las demos) | No hay respuesta del entorno en R3; el warmup usa la etiqueta antes de actuar (G6). | E2.6 (`entorno.py`, DE-8) |
| R4 · utilidad del ciclo | §4.2 · p. 62 | `bias_auditor*.py` registra «región 4» como auditoría | La R4 del agente (u_tarea) no existe; la auditoría de Ω es otra cosa. | E2.3 + E6 |
| R5 · registro de la teoría | §4.2 · p. 63; §4.4.4 · p. 92 | solo `pipeline.py:81` y `comun.py:197` | Fuera del agente (G1). | E2.3 |
| R6 · estadísticas | §4.2 · p. 63; §4.4.9 · pp. 117–122, Fig. 4.27 | — (G8); `region=6` mal usada (G12) | Ninguna estadística del LLC. | E2.4 (`estadisticas.py`) |
| R7 · evolución (Fig. 4.28) | §4.2 · p. 63; §4.4.10 · pp. 122–124; L-3 · pp. 267–270 | `monitor.py:97-124`, `agent.py:136-169` | Solo la reputación de equidad (G4). Faltan %CEA/%TNA y su definición por agente (sección 1.8). | E2.5 (DE-9: LLC ∧ gate de Ω) |
| Capas, escenarios y estados ganados | §4.2 · pp. 62–63; §4.5 · pp. 124–126 | `agent.py:58-65`; constructores (G2); `lifecycle.py:41-46` (G3) | El estado se fija; no hay escenarios por capa; Trained → TBO. | E2.5 + E2.6 |
| Cooperación (axioma [a], Alg. 4.9) | §4.3.1 · pp. 69–70; p. 109 | `sharing.py:108-122`, `agent.py:186-199` | Fiel (verificado el 03/07; `test_sharing_fuente.py`). Falta que conserve ΣP = K en modo LLC, a verificar en E3. | E3 |
| Colaboración (axioma [b], Alg. 4.10) | §4.3.1 · p. 70; pp. 112–116 | `sharing.py:125-139`, `agent.py:172-184` | Fiel. Falta `prov:wasDerivedFrom` de la teoría transferida en la ABox. | E3 + E4 |
| Gating por equidad de la compartición (extensión) | — (extensión del modelo, Def. 9) | `monitor.py:93-94`, `agent.py:112-133` | Sin brecha frente al LLC: es lo que agrega la tesis. | E3 (se muestra) |
| Teorías por rol del equipo | §4.2 (cada SAR); §4.3.1 (MultiSAR) | solo el Matcher (G1) | Parser, Bias Auditor y Explainer sin teorías. | E4 (sección 6 del handoff) |
| Traza por región y procedencia | — (aporte de la tesis, PROV-O) | `abox.py`: la decisión `prov:wasDerivedFrom` la teoría (l. 147) | Las teorías no tienen `prov:wasGeneratedBy` (ciclo y R5) ni procedencia de compartición; las regiones están mal rotuladas (G12). | E4 |
| Orquestación del DAG | — (lo exige el artículo, §5) | `core/orchestrator.py:30-48` (secuencial) | LangGraph declarado y no usado (G9). | E1 |
| Métricas de equidad por rol | — (pedido 5; decisión 5(b)) | `fairness.py` (DP, EO, Δ_esc, d_TV), por ventana | No hay e_rol por teoría ni U_rol con α. | E6 |

---

## 4. Preguntas para Kevin antes de E1 y E2

**P1 · Regla de evolución por agente (DE-9).** Por la observación de la sección 1.8, los valores de L-3 no se
pueden usar como umbrales de un agente. Propuesta para fijar en `configs/parada_tecnica.yaml` **antes de
correr**, con intervalo de estadísticas de n ciclos dentro de cada capa:

- **%CEA del agente:** (ciclos exitosos del intervalo actual − ciclos exitosos del primer intervalo de la
  capa) / ciclos exitosos del primer intervalo · 100. Es la lectura de la Fig. 4.28 con «inicial» =
  comienzo de la capa. Con 0 en el primer intervalo se usa el 1 como piso, y se declara.
- **%TNA del agente,** solo si recibió colaboración: teorías nuevas del intervalo actual / promedio de
  teorías nuevas de los intervalos previos de la capa · 100. Mide cuánto sigue generando; **bajo es mejor**.
- **Condición:** %CEA ≥ %RCE y, si hubo colaboración, **%TNA ≤ %RTN**. Conserva el sentido de la Fig. 4.28
  y de la p. 124 («genera una menor cantidad de teorías nuevas […] resultando el % TNA menor o igual» al
  %RTN). Se declara como adaptación a nivel de agente.
- **%RCE y %RTN como parámetros declarados.** Hay que fijarlos **antes de correr** y **no ajustarlos
  después**. No se pueden tomar de la tesis sin más: con estas definiciones a nivel de agente cambian de
  escala respecto de L-3.

¿Se aprueba esta definición, u otra, antes de E2?

**P2 · ¿Cuándo se evalúa la promoción?** La p. 63 asocia cada estado al *fin* de la capa, y la Fig. 4.28
promueve apenas se cumplen las condiciones y, si no, sigue hasta agotar los ciclos. Propuesta, según la
Fig. 4.28: evaluar al cierre de cada intervalo; promover si se cumple; si se agotan los ciclos de la capa sin
cumplir, el agente **queda** en su estado. ¿Ok?

**P3 · Utilidad de tarea por teoría** (consecuencia de DE-1). Con Sf dentro de la identidad, u_tarea queda
fija para cada teoría: para el Matcher vale 1 si A coincide con el resultado observado en Sf y 0 si no.
Entonces U(t) es constante por teoría. (Revisado el 08/10, punto 3 de P3: en la tesis U «indica la
utilidad de la teoría en función de la tarea asociada al SAR» y se calcula después de observar el
resultado, pp. 61–62; ver la sección 1.4.) En una celda, el
ranking U → P → K elige entre las variantes con U = 1 la de mayor P, es decir, el resultado observado más
frecuente. Es la lectura fiel; se confirma en E2 con la traza.

**P4 · Rescatar `dag.py` (G9).** Recomiendo proteger ahora el fuente de junio, que es reversible y local, sin
push. El comando es `git branch rescate/langgraph-junio b267323`, y conviene usarlo como punto de partida de
E1 (adaptado a `core/`, que no puede importar `instances/`). No lo hice: E0 no toca el repositorio más allá
de este documento. ¿Lo autorizás?

**P5 · Modo llm (E8).** `ollama` está instalado (`/opt/homebrew/bin/ollama`), pero el servicio no responde
en `localhost:11434`. Para E8 hay que levantarlo (`ollama serve`) y tener `llama3.1:8b`.

**Nota de nombres.** `configs/e0.yaml` y `experiments/e0_instrumento.py` son del «E0» de validación del
instrumento (julio), no de esta fase. Para no confundir, las salidas del Bloque E usan el prefijo
`parada_tecnica`.

---

## 5. Lo que ya está bien y se reutiliza (verificado)

- **Compartición fiel a la fuente:** `core/sharing.py:45-139` (Alg. 4.9 y 4.10, verificado contra pp. 109 y
  116; test `tests/test_sharing_fuente.py`).
- **Axiomas de estado:** `transfer_to` exige estado estrictamente superior (`agent.py:178-179`) y
  `cooperate_with` exige el mismo estado (`agent.py:192-193`), como §4.3.1 [a] y [b], pp. 69–70.
- **Gating por equidad:** reputación (Def. 9), historia mínima del donante (A9, `can_donate`, `agent.py:130`)
  y gate certificado con `m_min` (C7).
- **Planificador LLC casi listo:** `TheoryBase.select` + `applicable` (`theory.py:191-209`).
- **Ontología:** ABox RDF/PROV-O con IRIs por clave (C3, C13), SHACL, SPARQL y M2M de teorías.
- **Instrumental de equidad y escenarios:** `human_sim` (modos `oracle`, `noisy` y `biased`; `human_sim.py:21`)
  para la respuesta del entorno en WIO (DE-8), `escalation_disparity` (C5), `dtv_lower_bound` (B3) y
  `core/committee.py`.
- **Separación de capas:** `tests/test_decoupling.py` garantiza que el `core/` no importa `instances/`.

---

## 6. Qué no se hizo en E0

- No se modificó código, configuración ni tests. El único archivo nuevo es este documento, en la rama
  `eje1/bloque-e`, sin push ni merge.
- No se corrieron demos. La suite se corrió como control: 146 passed, 1 skipped.
- No se recuperó `dag.py` ni se creó ninguna referencia nueva en git: queda como pregunta P4.

**Punto de control ⏸:** Kevin revisa este diagnóstico y responde P1–P5 antes de E1.
