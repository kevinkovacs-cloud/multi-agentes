# Bloque E — «Parada técnica»: la prueba de concepto funcionando como ciclo de vida

**Fecha:** 08/10/2026 · **Para:** Claude Code (repositorio local `~/Downloads/moav-hr 2`) y, en las secciones 1 a 3, para quien retome desde una sesión nueva de Claude chat.
**Base:** rama `eje1/formalizacion-v2` en `58ce027` (146 passed, 1 skipped al 30/09; verificarlo antes de empezar). `main` = `9ec2185`, no se toca.

---

## 0. Cómo usar este documento

- **Claude Code:** leerlo completo. Empezar por **E0 (diagnóstico, sin tocar código)** y detenerse en cada punto de control marcado **⏸**, donde Kevin revisa antes de seguir. Un commit por ítem, con `pytest -q` en verde.
- **Claude chat (sesión nueva):** leer las secciones 1 a 3 y el `README.md` del proyecto (sección 0). Cuando Claude Code termine, Claude chat revisa el informe generado y arma el material para el encuentro con la dirección (sección 10).

### 0.1 Dónde está cada archivo (rutas en la Mac de Kevin)

Claude Code **no** tiene acceso al proyecto de claude.ai. Todo lo que este documento cita está en estas rutas locales. Leer primero los marcados con ★.

**Repositorio** — `/Users/kevinkovacs/Downloads/moav-hr 2/`

- ★ este handoff: `HANDOFF_CLAUDE_CODE_bloqueE_parada_tecnica_2026-10-08.md`
- ★ `ESTADO.md` (estado del PoC, Bloques C y D, pendientes)
- `DERIVA_DEMO.md`
- `docs/demos_direccion/NUMEROS_PARA_PLACAS.md` (resultados del Bloque D)
- handoffs anteriores, en la raíz: `HANDOFF_CLAUDE_CODE_bloqueC_*.md` y `HANDOFF_CLAUDE_CODE_bloqueD_demos_direccion_2026-09-29.md`

**Tesis** — `/Users/kevinkovacs/Desktop/Investigacion/Tesis/`

- ★ `Claude outputs/README_PROYECTO_estado_2026-10-08.md`: copia del README del proyecto de claude.ai, cuya sección 0 es el estado vigente.
- ★ `Claude outputs/HOJA_DECISIONES_DIRECCION_5_2026-09-29.md`: las cinco decisiones de la dirección.
- `Claude outputs/MATRIZ_recomendaciones_directores_2026-09-29.md`
- ★ `enviar plan de tesis/MAIL_Ierache_Becerra_parada_tecnica_recibido.txt`: el pedido textual.
- `enviar plan de tesis/MAIL_Jorge_hoja_decisiones_post_CACIC.txt`: el mail que mandó Kevin.
- `BITACORA_TESIS.md`: bitácora; la entrada «08/10 (a)» es la de este bloque.
- `Paper CACIC 2026/Paper_CACIC_2026_camera_ready_final.pdf` y `Paper CACIC 2026/paper.tex`: el artículo publicado.

**Fuentes** — `/Users/kevinkovacs/Desktop/Investigacion/academico/doctorado/`

- ★ `Bibliografia para leer/01 · LLC de Ierache y trabajos del grupo/Ierache_2010_Tesis-doctoral-LLC__leer_pp59-63_105-116_120_233.pdf`: la tesis completa de Ierache, 300 págs., la vara de este bloque.
- `Bibliografia para leer/00_HALLAZGOS_de_la_lectura.md`: hallazgos de la lectura (Bower 2017, Li-Gao-Wang 2026, etc.).
- `GENESIS_2026-09-23/REVISION_GENESIS_v2_2026-09-29.md`: revisión de la matemática.

Cuando este documento dice «hoja» o «decisión N», se refiere a `HOJA_DECISIONES_DIRECCION_5_2026-09-29.md`. Cuando dice «README del proyecto», se refiere a `README_PROYECTO_estado_2026-10-08.md`.

---

## 1. Contexto mínimo

- **Tesis:** modelo genérico de ciclo de vida para el aprendizaje de agentes autónomos basados en equidad. Extiende el LLC de Ierache (2010) de robots a agentes LLM y agrega el Monitor de Equidad Ω. La selección de personal es **solo el dominio de experimentación**.
- **Kevin es estudiante de doctorado** (doctorando recién cuando se apruebe el plan). Director: Dr. Jorge Ierache. Codirector: Dr. Martín Becerra.
- **Artículo** «Modelo de ciclo de vida para agentes LLM basados en equidad» (Kovacs, Ierache y Becerra): XXXII CACIC, WASI. Presentado el 06/10/2026 y aprobado para publicación.
- **Hoja de cinco decisiones de formalización:** Kevin la envió a la dirección después del CACIC, junto con dos antecedentes (Bower et al. 2017; Li, Gao y Wang 2026). Jorge acusó recibo. Las decisiones son: (1) regla del Monitor; (2) planificador y contadores P y K; (3) b_in; (4) equidad como «metapieza»; (5) «utilidad ponderada por equidad». Detalle en `Tesis/Claude outputs/HOJA_DECISIONES_DIRECCION_5_2026-09-29.md` (ver la sección 0.1).
- **Respuesta conjunta de Jorge y Martín (registrada el 08/10/2026):** antes de esas decisiones piden una **parada técnica**, es decir, asegurar que la prueba de concepto funcione desde el punto de vista del **ciclo de vida de los agentes**. Las decisiones quedan en espera; ver la sección 3.

---

## 2. Pedido textual de la dirección

> Buenas noches Kevin, vemos con Jorge que antes de los detalles mencionados en el correo, necesitamos hacer una parada técnica para asegurar la prueba de concepto este funcional desde el punto de vista del ciclo de vida de agentes.
>
> Se necesita demostrar en el caso de aplicación:
> 1 - Correr un caso que genere una teoría. Demostrar punto a punto como avanza en el ciclo de vida.
> 2a - Como se coopera, colabora y transfiere la teoría generada a un agente novato.
> 2b - Como se rankea y se recupera la teoría generada anteriormente de un propio agente.
> 3 - Demostrar el funcionamiento multiagente de esta colaboración. En la prueba de concepto el equipo DAG tiene diferentes roles, como maduran otro equipo DAG a que se le transfiere la teoría.
> 4 - Tracear cada etapa del ciclo de vida para generar cada instancia de teoría de aprendizaje de cada rol de agente del equipo DAG. Que situación inicial hay, que acciones se tomaron y cada una de los componentes de la teoría según su rol.
> 5 - Definir las métricas de equidad que van a tener la función de utilidad de cada agente según su rol.
>
> Avancemos en estos puntos y cuando tengas listos avances, vemos de coordinar un encuentro para evaluar la implementación y trazabilidad de los resultados. Luego de acuerdo a esto se formalizará el plan o se tendrá que efectuar los ajustes necesarios.
>
> Trabaja estos puntos con avances sustentables, con tranquilidad que es mas importante asegurar el funcionamiento en esta etapa para llevar adelante el plan y asegurar el éxito.
>
> Jorge y Martín.

---

## 3. Lectura del pedido

1. **«Funcional desde el ciclo de vida» significa el LLC de Ierache tal como está en su tesis**, no nuestras abstracciones. La vara es la fuente: §4.1.2 (teoría), §4.2 (siete regiones, capas, estados), §4.3.1 (axiomas de compartición), §4.4.6 (comparación de teorías), §4.4.7 (planificador, Fig. 4.21), §4.4.9 (estadísticas), §4.4.10 (evolución, Fig. 4.28) y Anexo L-3 (parámetros de rendimiento). El PDF completo (300 págs.) está en la copia de Kevin: `~/Desktop/Investigacion/academico/doctorado/Bibliografia para leer/01 · LLC de Ierache y trabajos del grupo/Ierache_2010_Tesis-doctoral-LLC__leer_pp59-63_105-116_120_233.pdf`. En algunos tramos la página del PDF y la impresa difieren en uno: **citar la sección o figura y la página impresa**.
2. **El pedido tiene prioridad sobre las cinco decisiones, pero las toca.** Los puntos 2b y 4 dependen de la semántica de P y K y del planificador (decisión 2). El punto 4 toca el registro E(t) (decisión 4). El punto 5 pide definir la equidad **dentro de la función de utilidad de cada agente**, lo que inclina la decisión 5 hacia su opción (b). Este bloque **implementa como propuesta** las opciones recomendadas en la hoja, en modo opcional y sin borrar lo existente, para que la dirección las evalúe funcionando. No las adopta en su nombre.
3. **«Con tranquilidad» y «avances sustentables»:** primero el rol decisor de punta a punta (puntos 1 y 2b), después la compartición (2a), después todos los roles y los equipos (3 y 4) y por último la equidad por rol (5). Hay puntos de control con Kevin entre fases.

---

## 4. Diagnóstico previo (E0 lo confirma o lo refuta con archivo y línea)

Lo que hoy **no** cumple el pedido. Revisado por Claude chat el 08/10 sobre `58ce027` y la tesis de Ierache:

| # | Hallazgo | Evidencia | Qué exige el LLC (Ierache 2010) |
|---|---|---|---|
| G1 | **El pipeline no ejecuta el ciclo de vida.** Los `run()` de los agentes hacen R1–R2 (y parte de R4); el aprendizaje (R5) y la evolución (R7) se hacen afuera, en los scripts de demos (`experiments/demos_direccion/comun.py: ejecutar_tarea`) o en `warmup`. Solo el Matcher tiene teorías. | `instances/hr/*.py`, `comun.py` | §4.2: cada SAR recorre las 7 regiones en cada ciclo percepción-acción. |
| G2 | **El estado de madurez se fija en el constructor**: Parser `training_runs=5` + WIO bootstrap → Mature; Matcher `training_runs=4` → Trained; BiasAuditor demo → Mature; Explainer `training_runs=1` → Novice. No se gana recorriendo capas. | `parser_agent.py`, `semantic_matcher.py:23`, `bias_auditor.py:21`, `explainability_agent.py:10` | §4.2 (pp. 62–63): Born al inicio de BIO; Newbie al terminar BIO; Trained al terminar TBO; Mature al terminar WIO. |
| G3 | **Capa activa mal mapeada:** el código pone Novice y Trained en TBO y Mature en WIO. | `core/lifecycle.py: _ACTIVE` | §4.2 (p. 62): BIO-escenario (Born→Newbie), TBO-escenario (Newbie→Trained), WIO-escenario (Trained→Mature). |
| G4 | **Regla de evolución distinta:** `gate_evolution` solo mira la reputación de equidad. | `core/monitor.py: gate_evolution`, `core/agent.py: advance` | §4.4.10, Fig. 4.28: promueve si %CEA ≥ %RCE (ciclos exitosos) y, si recibió colaboración, %TNA ≤ %RTN (teorías nuevas). Si no, sigue en la capa hasta completar n ciclos. Los umbrales están en el Anexo L-3. |
| G5 | **Semántica de P y K distinta (decisión 2):** una teoría por (Si, A), con P = aciertos y K = usos. Por eso nunca aparecen teorías «similares» (D3: 0). | `core/theory.py: Theory.reinforce`, `core/agent.py: learn` | §4.1.2 (p. 60): P = veces que con Si se ejecutó A y se obtuvo Sf; K = veces que con Si se ejecutó A. Al confirmarse una teoría suben su P y su K y el K de las complementarias (misma Si y A). Invariante: ΣP = K en la celda. |
| G6 | **Base sembrada con la etiqueta de verdad:** `warmup` siembra con los mismos candidatos y `true_qual`. | `instances/hr/pipeline.py: warmup` | §4.1.1 (p. 59): la teoría se forma después de ejecutar la acción y observar la situación resultante. |
| G7 | **El planificador no restringe a la misma Si:** `retrieve` filtra por similitud y ordena por (U, P, K). | `core/retrieval.py`, `ESTADO.md` (pendiente del Bloque D) | §4.4.6: las situaciones se comparan por discretización con umbral (exacto, umbral común o individual). §4.4.7 y Fig. 4.21: el planificador ranking ordena las teorías aplicables por U, luego P, luego K. Sin plan válido, «acción al azar». |
| G8 | **No hay estadísticas de la región 6.** | — | §4.4.9: situaciones, teorías acumuladas, teorías por intervalo de U y de P/K, teorías nuevas, teorías exitosas (U > 0,75), ciclos exitosos (ciclo que termina con una teoría de U > 0,75), planes y azares. |
| G9 | **LangGraph:** el artículo (§5) y el README dicen «implementación en Python sobre LangGraph», pero `core/orchestrator.py` es un bucle secuencial. Ninguna rama importa `langgraph` en `src/`: solo `langchain_ollama`, en `core/llm.py`. Hay un `src/moav_hr/pipeline/__pycache__/dag.cpython-312.pyc` huérfano de junio, sin fuente. | `git grep -n -i langgraph <rama> -- src` | Lo exige el propio artículo. |
| G10 | **Auditor demostrativo con etiqueta y oráculo** (`bias_auditor.py`). Ya existe el experimental, sin oráculo (`bias_auditor_exp.py`). | `ESTADO.md` (alcance del modo sim) | — |

Lo que **ya está bien** y se reutiliza:

- `core/sharing.py` es fiel a los Alg. 4.9 y 4.10 (igual, similar y nueva).
- `transfer_to` exige estado estrictamente superior y `cooperate_with` exige el mismo estado (axiomas de §4.3.1, pp. 69–70).
- El gating por reputación (Def. 9, A9) y el registro de auditoría RDF/PROV-O con SHACL y SPARQL.
- Los IRIs por clave (C3, C13) y la exportación M2M de teorías.
- `human_sim` (revisión humana simulada), `escalation_disparity` (C5), `dtv_lower_bound` (B3) y `core/committee.py`.

---

## 5. Decisiones por defecto de este bloque

Kevin puede cambiarlas antes de E2. Todas se presentan a la dirección como **propuesta funcionando**, no como decisión tomada.

- **DE-1 · Semántica LLC de P y K** (decisión 2, opción a). Es un modo opcional `semantica="llc"` en la maquinaria nueva. La semántica actual queda como default del código existente, para no romper `demo_caso.py`, `run_poc.py`, los demos del Bloque D ni sus tests.
- **DE-2 · Orden del planificador:** el de la Fig. 4.21 (U desc, P desc, K asc), con desempate final determinista (recencia, id). Aplicabilidad: la **misma celda de Si** bajo la cuantización Q, que es el análogo de la comparación por umbral de §4.4.6. La similitud continua (coseno o embeddings) queda como **extensión declarada** para situaciones en lenguaje natural. Solo se usa como respaldo cuando la celda está vacía, y cada uso se registra.
- **DE-3 · «Azar» en un dominio sensible:** cuando no hay teoría aplicable, el agente actúa con su **operador BIO** (la regla del diseñador en sim, o el LLM con el system prompt en modo llm), no al azar, y la estadística «azares» lo cuenta. Es una adaptación declarada: decidir al azar sobre personas no es aceptable, ni siquiera en simulación.
- **DE-4 · Registro E(t)** (decisión 4, opción a). Es un metadato derivado de la procedencia y **fuera de la tupla** ⟨Si, A, Sf, P, K, U⟩. El atributo protegido vive solo en el plano de auditoría (Ω y E(t)), **nunca** en Si, en A ni en los prompts.
- **DE-5 · Utilidad por rol con equidad** (punto 5; decisión 5, opción b): U_rol(t) = α·u_tarea(t) + (1 − α)·e_rol(t), con α configurable. Cada demo muestra **α = 1** (LLC puro) junto a **α = 0,5** (con equidad). e_rol solo se usa cuando la teoría tiene usos suficientes en **ambos** grupos (`m_min`, configurable); si no, se usa α = 1 y se registra.
- **DE-6 · El rol Bias Auditor** (Ω en la cadena) tiene base de teorías, pero su **regla de intervención no aprende**: sigue siendo la del certificado (LCB > τ_b, configuración BIO). Sus teorías registran situación de la ventana → intervención → resultado de la revisión humana. Son las «teorías de sesgo» que Jorge propuso conservar para auditoría (17/07/2026). Sirven para su utilidad, su evolución y la auditoría, nunca para relajar el bloqueo.
- **DE-7 · Orchestrator** sin base de teorías: es infraestructura de la capa BIO y se declara así en la traza.
- **DE-8 · Entorno simulado por capa,** análogo al simulador del LLC (Webots, §4.6): escenarios BIO, TBO y WIO con candidatos sintéticos generados con semilla, uno por capa y con complejidad distinta, como en §4.5. El entorno responde **después** de la acción (R3), nunca antes. En BIO y TBO, con la etiqueta del escenario de entrenamiento. En WIO, con la revisión humana simulada (`human_sim`, modo `noisy`), que puede equivocarse. Las reglas del entorno se fijan y se documentan **antes** de correr, y no se ajustan después para que algo «dé».
- **DE-9 · %RCE y %RTN:** se leen en el Anexo L-3 y se transcriben con su página. Si no son trasladables (están definidos para el e-puck), se fijan **antes de correr** en `configs/`, se declaran como parámetros y nunca se ajustan a posteriori. La regla de evolución del bloque es **LLC (Fig. 4.28) ∧ gate de equidad de Ω**: la extensión agrega una condición, no reemplaza la del LLC.
- **DE-10 · LangGraph:** el DAG se orquesta con `StateGraph` en un módulo genérico del `core`. El orquestador secuencial actual se conserva para `main` y los demos viejos. Un test de equivalencia muestra que, en el lote de la PoC, ambos producen las mismas decisiones y el mismo orden de eventos.
- **DE-11 · Modo de ejecución:** sim para los tests y para todos los números del informe. Si Ollama está disponible en la máquina de Kevin, una corrida de P1 y P4 en modo llm (Llama 3.1 8B local) se reporta **por separado**, sin mezclar números.

---

## 6. Definición de las teorías por rol (propuesta para validar con la dirección)

Esta es la base de los puntos 4 y 5. Reglas comunes:

- Si es discretizada y **no** contiene atributos protegidos.
- Un ciclo es «exitoso» si termina con una teoría de U > 0,75 (§4.4.9).
- e_rol se calcula sobre E(t) o sobre la ventana, siempre en el plano de auditoría.

| Rol | Si (R1: qué percibe) | A (R2: acciones posibles) | Sf (R3: qué observa y quién se lo da) | u_tarea (R4) | e_rol (R4, equidad) |
|---|---|---|---|---|---|
| **Parser** | Rasgos del documento de entrada: formato (texto, HTML o JSON), banda de campos detectados y sinónimos sin resolver. | Estrategia de extracción: reglas estrictas, diccionario de sinónimos o extracción con LLM (solo en modo llm). Hay que implementar al menos dos variantes a partir del parser actual. | Completitud del perfil: completo, parcial o fallido, validada contra un shape SHACL del perfil. Fuga de atributo protegido: sí o no. | 1 si es completo y sin fuga; 0,5 si es parcial; 0 si falla o hay fuga. | Brecha de completitud de extracción entre grupos en la ventana. Métrica de auditoría adicional: `dtv_lower_bound` del canal proxy (B3). |
| **Semantic Matcher** | `build_si`: skills, banda de experiencia, educación, antigüedad mínima. | ADVANCE o REJECT. | Calificado: sí o no. En TBO, etiqueta del escenario de entrenamiento; en WIO, resultado de la revisión humana simulada. | 1 si la acción fue correcta para el resultado observado; 0 si no. | Equalized odds en la ventana (máximo de ΔTPR y ΔFPR). Por teoría, ê(t) = 1 − \|tasa de error del grupo 1 − tasa de error del grupo 2\| sobre E(t). |
| **Bias Auditor** (Ω en la cadena) | Situación de la ventana: banda de n por grupo, banda de la brecha observada y si LCB > τ_b. | LIBERAR o DERIVAR. La decide la regla certificada, no la teoría (DE-6). | Resultado de la revisión humana de la ventana derivada (sesgo confirmado: sí o no). Para ventanas liberadas, la disparidad medida después en WIO. | 1 si la intervención fue correcta; 0 si no. | Paridad de derivación entre grupos: `escalation_disparity` (C5). |
| **Explainer** | Tipo de decisión (avanza, rechaza o deriva), destinatario (regulador o usuario) y banda de motivos disponibles. | Estrategia de explicación: por factores, contrafáctica o regulatoria. Hay que implementar variantes mínimas. | Completitud verificada contra el grafo RDF con `explain_from_rdf`: sí o no. | Completitud: 1 o 0. | Brecha de completitud de la explicación entre grupos. |
| **Orchestrator** | — | — | — | — | Sin teorías (DE-7). Registra la decisión final y el escalamiento. |

**Advertencia formal (hoja, decisión 4).** En el Matcher la acción de la teoría *es* la decisión. Dentro de una celda todos reciben la misma acción, así que la paridad demográfica **por teoría** es trivial. Por eso e_rol por teoría usa paridad de **errores**, que necesita Sf. La disparidad de trato entre grupos surge de **qué** teorías se aplican a cada grupo, y se mide en la ventana. El informe lo explica con un ejemplo corrido.

**Variabilidad del entorno.** Para Parser y Explainer, el entorno simulado tiene que hacer que las estrategias rindan distinto según la Si. Si no, las teorías son triviales. Las tasas se fijan antes de correr, se documentan en `instances/hr/entorno.py` y se citan en el informe.

---

## 7. Reglas

1. **Rama** `eje1/bloque-e`, creada desde `eje1/formalizacion-v2` (`58ce027`). `main` y las ramas `eje1/bloque-c` y `eje1/bloque-d` no se tocan. **Sin push ni merge** hasta que Kevin lo autorice.
2. **Commits:** uno por ítem, con `pytest -q` en verde antes de cada uno. El conteo de tests sube y se reporta.
3. **No romper lo existente:** `demo_caso.py`, `run_poc.py` y `experiments/demos_direccion/*` siguen dando la misma salida (verificarlo contra `DERIVA_DEMO.md` y `NUMEROS_PARA_PLACAS.md`). Lo nuevo entra por módulos y opciones nuevas.
4. **Ningún número escrito a mano.** Todo lo que aparezca en JSON, figuras, Markdown o HTML sale de correr el código. Los resultados inesperados se reportan tal cual, en una sección «Resultados que no fueron los esperados».
5. **Rótulos obligatorios en cada salida:**
   - «ilustrativo, entorno simulado (modo sim); no es evidencia experimental»;
   - «semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección».
6. **Sin oráculo en la decisión:** la etiqueta del escenario solo entra como respuesta del entorno en R3, después de la acción. En el Bloque E no hay `warmup` con etiquetas.
7. **Atributo protegido fuera del plano de decisión** (DE-4). Un test lo verifica sobre Si, A, los prompts y los few-shot.
8. **El core no importa `instances/`** (ya hay un test de decoupling; mantenerlo).
9. **Nombres:**
   - en el código puede seguir la sigla MOACV y el literal `novato`;
   - en documentos y salidas: «el modelo», «Monitor de Equidad», estados Born, Novice, Trained y Mature;
   - «newbie» solo al citar a Ierache.
10. **Nada de teoría de juegos** (ni valores de Shapley ni equilibrios): es trabajo futuro de la tesis.
11. **Citas a Ierache 2010** con sección, figura y página impresa, verificadas en el PDF. Si algo no se puede verificar, se marca `[verificar]` y no se completa de memoria.
12. **Figuras legibles:** matplotlib a `dpi=200`, cuerpo ≥ 12 pt, títulos ≥ 14 pt, colores oscuros, sin gris claro, unos 1800 px de ancho.
13. **Ubicación de los archivos:**
   - código nuevo en `src/moav_hr/core/` (genérico) e `instances/hr/` (dominio);
   - scripts en `experiments/parada_tecnica/`;
   - salidas en `docs/parada_tecnica/` (JSON, PNG, MD, HTML y TTL, que se commitean);
   - tests en `tests/test_bloquee_*.py`;
   - configuración en `configs/parada_tecnica.yaml`.

---

## 8. Fases e ítems

### E0 · Diagnóstico (sin cambios de código) ⏸

Confirmar o refutar G1 a G10 con archivo y línea, y correr la suite. Leer en el PDF de Ierache §4.4.6, §4.4.7 (Fig. 4.21), §4.4.9, §4.4.10 (Fig. 4.28) y el Anexo L-3. Transcribir:

- las fórmulas de %CEA, %TNA, %RCE y %RTN;
- los valores usados por Ierache;
- la definición de «ciclo exitoso» y de «azar»;
- el orden del planificador ranking.

Entregar `docs/parada_tecnica/E0_DIAGNOSTICO.md`, con el mapa **concepto del LLC → sección y página → código actual → brecha → ítem del Bloque E**. **Parar y esperar a Kevin.**

### E1 · Orquestación con LangGraph (G9)

- `core/grafo.py`: construye un `StateGraph` de LangGraph a partir de la lista de agentes en orden topológico, el Monitor y el finalizador. Es genérico, sin dominio.
- El comité es un nodo que agrega a sus miembros. Mantener `core/committee.py`.
- `HRPipeline(..., orquestador="langgraph" | "secuencial")`: el default sigue en `"secuencial"` para no mover la salida de los demos viejos. El Bloque E usa `"langgraph"`.
- Test de equivalencia sobre los 12 candidatos de la PoC: mismas decisiones y mismos eventos de trail en el mismo orden.
- Borrar el `.pyc` huérfano de `src/moav_hr/pipeline/` (está fuera de git; verificarlo antes).

### E2 · Núcleo del ciclo de vida para el rol decisor (puntos 1 y 2b) ⏸

1. **Semántica LLC (DE-1, G5):** `learn_llc(si, a, sf)` aplica las reglas de §4.1.2:
   - teoría igual → P + 1, K + 1, y K + 1 en las complementarias de la celda (Si, A);
   - teoría nueva → P = 1 y K = K de la celda, después del incremento;
   - el invariante **ΣP = K** por celda se verifica en tests y, como restricción, en SHACL (es el I4 pendiente).

   `sharing.py` tiene que conservar el invariante en el modo LLC: verificarlo con tests; si no lo conserva, documentarlo y corregirlo solo en ese modo.
2. **Planificador LLC (DE-2, G7):** `core/planificador.py`:
   - teorías aplicables = misma celda Q(Si);
   - orden de la Fig. 4.21;
   - respaldo por similitud (extensión) solo con la celda vacía;
   - si tampoco hay similitud, operador BIO (DE-3).

   Cada decisión registra las candidatas, sus (U, P, K), la elegida y el motivo: celda, similitud o BIO.
3. **Ciclo de 7 regiones dentro del agente (G1):** `core/ciclo_llc.py` define una interfaz por rol (`percibir`, `actuar`, `observar`, `utilidad`) y el motor ejecuta R1 a R7 en cada ciclo. Cada región emite un evento de trail con `ciclo`, `capa`, `estado`, `region` y sus valores (Si, candidatas, A, Sf, u, U, P, K, estadísticas, decisión de evolución).
4. **Estadísticas R6 (G8):** `core/estadisticas.py` con la lista de §4.4.9, más las de equidad (fair(W), e_rol).
5. **Capas, escenarios y evolución (G2, G3, G4, DE-8, DE-9):**
   - el estado se **gana**: Born recorre el escenario BIO, Novice el TBO y Trained el WIO;
   - al final de cada capa, o antes si se cumplen las condiciones, se evalúa la regla de la Fig. 4.28 ∧ el gate de Ω;
   - `_ACTIVE` se corrige solo en el modo nuevo, o se agrega un mapa LLC aparte si cambiarlo rompe tests viejos (documentarlo).
6. **Entorno:** `instances/hr/entorno.py` genera escenarios BIO, TBO y WIO con semilla y documenta sus reglas.
7. **Demo P1** `experiments/parada_tecnica/p1_teoria_punto_a_punto.py`. Un Matcher en Born, con la base vacía:
   - **ciclo 1:** un candidato concreto, R1 a R7 con todos los valores y la teoría T* que nace en R5 (IRI, P, K, U);
   - **ciclos siguientes:** recorre BIO → TBO → WIO con transiciones de estado ganadas, mostrando en cada evaluación %CEA, %TNA, umbrales y gate de Ω;
   - **salidas:** `p1_traza_ciclo1.md` (tabla región por región), `p1_linea_de_tiempo.png` (estado, teorías acumuladas, teorías nuevas y ciclos exitosos por ciclo) y `p1.json`.
8. **Demo P2b** `p2b_planificador.py`. El mismo agente, más adelante:
   - (i) un caso con la misma Si que T*: tabla de candidatas de la celda ordenadas por (U, P, K), la elegida y por qué;
   - (ii) un caso con Si nueva: respaldo por similitud, declarado como extensión;
   - (iii) un caso sin nada aplicable: operador BIO, contado como azar.

   Mostrar α = 1 y α = 0,5 si la U con equidad cambia la elegida. Si no la cambia, decirlo.

**Parar y esperar a Kevin** con P1 y P2b corridos. Claude chat revisa la traza antes de seguir.

### E3 · Compartición de la teoría generada (punto 2a)

`p2a_compartir.py`, con **la misma T*** (mismo IRI y clave) y en modo LLC:

- **Cooperación** entre dos Matchers en el **mismo estado**, por ejemplo dos Novice de equipos distintos (§4.3.1, axioma [a]).
- **Colaboración** de un Matcher Trained o Mature a un Matcher **Novice** (axioma [b]). Es la «transferencia a un agente novato» del pedido.
- Para cada operación:
  - el gate de Ω: r ≥ τ y `can_donate`;
  - la clasificación igual, similar o nueva, con P y K antes y después;
  - el invariante ΣP = K;
  - la cadena `prov:wasDerivedFrom` de T* en el receptor.
- Con la semántica LLC y el ruido de WIO tienen que aparecer **teorías similares** (es el D8 pendiente). Si no aparecen, reportarlo.
- Contraejemplos: cooperación entre estados distintos y colaboración hacia un estado superior, ambas rechazadas con el axioma citado.
- Mostrar el **efecto** en el receptor: la siguiente vez que recibe un caso con la Si de T*, el planificador la elige.

### E4 · Todos los roles con su ciclo de vida y traza completa (punto 4) ⏸

- Implementar las teorías por rol de la sección 6: Parser, Bias Auditor (DE-6) y Explainer, con al menos dos estrategias donde haga falta. El Orchestrator queda sin teorías.
- Extender la ABox:
  - cada teoría con `prov:wasGeneratedBy` (actividad = ciclo i, región 5), la asociación al agente y al rol;
  - `prov:wasDerivedFrom` cuando viene de compartir;
  - nodos por región del ciclo con sus valores.

  Agregar shapes SHACL nuevos (incluido ΣP = K) y consultas SPARQL:
  - genealogía de una teoría;
  - qué teorías de qué roles intervinieron en la decisión X;
  - teorías por rol y estado;
  - e_rol por rol.
- **Demo P4** `p4_traza.py`. Un equipo DAG completo procesa casos y, para cada rol, imprime y exporta:
  - la situación inicial;
  - las candidatas y la acción tomada;
  - la situación final;
  - P, K y U;
  - la región en que se registró y el estado del agente.

  **Salidas:**
  - `p4_traza_<caso>.md` y `p4_traza_<caso>.html` (legible para la reunión, con una tabla por rol);
  - `p4_equipo.ttl`;
  - `p4_shacl.txt` (conforme o no);
  - `p4_sparql.md` (consultas y resultados).

**Parar y esperar a Kevin.**

### E5 · Equipos DAG: un equipo maduro hace madurar a otro (punto 3)

`p3_equipos_dag.py`:

- **Equipo A:** recorre BIO → TBO → WIO hasta que sus roles llegan a Trained o Mature, según la regla.
- **Equipo B (Born):** recibe colaboración rol por rol del A (parser→parser, matcher→matcher, …). Solo entre agentes del mismo rol; está declarado como regla del modelo, porque las teorías de un rol no tienen sentido en otro.
- **Equipo B0 (control):** las mismas semillas y escenarios, sin colaboración.
- **Cooperación:** dos equipos en el mismo estado, B y C Novice.
- **Métricas por rol y por equipo:**
  - ciclos hasta cada cambio de estado;
  - teorías nuevas por capa (%TNA);
  - ciclos exitosos (%CEA);
  - fair(W) y e_rol;
  - compartidas aceptadas y rechazadas por Ω.

  Son las métricas primarias del propio LLC (§4.2, R7; §4.4.10).
- **Figura** `p3_maduracion_equipos.png`: líneas de tiempo de estado por rol, B vs B0. Si B no madura antes que B0, **reportarlo tal cual** y analizar por qué. Nada se ajusta para que dé.

### E6 · Métricas de equidad por rol (punto 5)

- `core/equidad_roles.py`: e_rol según la sección 6, U_rol con α y el registro E(t) (DE-4, DE-5).
- `docs/parada_tecnica/METRICAS_EQUIDAD_POR_ROL.md`, escrito para la dirección. Para cada rol:
  - la definición y la fórmula;
  - qué datos usa y de qué plano (decisión o auditoría);
  - el mínimo de usos;
  - los límites, incluida la advertencia formal de la sección 6;
  - los valores corridos;
  - un caso donde α = 0,5 cambie la teoría elegida, o la constancia de que no ocurrió.
- `p5_metricas_equidad.py` genera los números.

### E7 · Informe y cierre ⏸

- `experiments/parada_tecnica/generar_todo.py` corre P1, P2a, P2b, P3, P4 y P5 y escribe `docs/parada_tecnica/INFORME_PARADA_TECNICA.md`. Para cada punto del pedido incluye:
  - qué se demuestra;
  - el comando para reproducirlo;
  - los números clave;
  - las figuras;
  - los rótulos;
  - los resultados inesperados.
- `docs/parada_tecnica/LEEME_REUNION.md`: guion de 10 líneas para mostrar en vivo, con los comandos y las salidas.
- `ESTADO.md`: sección «Bloque E» con lo hecho, lo pendiente y lo sujeto a la dirección.
- **Parar y esperar a Kevin** para push.

### E8 · Opcional: modo llm

Solo si Ollama con Llama 3.1 8B corre en la máquina de Kevin: P1 y P4 en modo llm. Las salidas van separadas en `docs/parada_tecnica/llm/`, con el rótulo «modelo local sin calibrar». No se comparan números con el modo sim.

---

## 9. Qué NO hace este bloque

- No valida la conjetura μ < 1 ni corre experimentos del Eje 2. No usa FairCVtest, JobFair ni FINDHR.
- No modifica el artículo, el plan ni la presentación.
- No adopta las decisiones de la hoja: las implementa como opción para que la dirección las evalúe.
- No implementa teorías mutantes. El LLC las menciona como variante del planificador (SARr M); se declaran fuera de alcance.
- No introduce teoría de juegos.

---

## 10. Después del Bloque E (Claude chat)

1. Revisar `INFORME_PARADA_TECNICA.md` contra el código y la fuente: citas de Ierache, rótulos, números generados y lenguaje sin sobreventa.
2. Armar el material del encuentro:
   - un deck corto con el tipo Slides (5 placas, una por punto, más contexto y preguntas);
   - la traza HTML de P4 para mostrar en vivo.
3. Mail a Jorge y Martín para coordinar el encuentro, formal y breve.
4. Preguntas que el encuentro tiene que cerrar:
   - definición de Si, A y Sf por rol (sección 6);
   - α y `m_min`;
   - %RCE y %RTN;
   - si el Bias Auditor aprende (DE-6);
   - adopción de la semántica LLC de P y K (decisión 2);
   - si la similitud queda como extensión del planificador.
5. Actualizar la bitácora, el README del proyecto y el plan solo después de lo que diga la dirección: «se formalizará el plan o se tendrá que efectuar los ajustes necesarios».

---

## 11. Estado general para retomar (al 08/10/2026)

- **Pendientes administrativos:**
  - tabla del §7 del plan en formato plantilla (faltan Bloque y horas de cada curso);
  - notas firmadas de los Anexos B y C;
  - CVar de Ierache;
  - referencia de las actas del CACIC 2026 cuando salgan (SEDICI, con ISBN; ver la bitácora del 06/10).
- **Errata del paper** («Vargas» → «Vargo»; Borah «≥≈50 %»): solo si hay instancia de versión final o selección para Springer.
- **Fuentes de verdad:**
  - `README.md` del proyecto (sección 0); copia local en `Tesis/Claude outputs/README_PROYECTO_estado_2026-10-08.md`;
  - `Tesis/BITACORA_TESIS.md`;
  - `ESTADO.md` del repo;
  - este documento.
