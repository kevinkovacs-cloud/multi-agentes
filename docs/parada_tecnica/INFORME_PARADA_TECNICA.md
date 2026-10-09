# Parada técnica: la prueba de concepto como ciclo de vida (Bloque E)

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

Informe para la dirección (Jorge Ierache y Martín Becerra). Selección de personal es el dominio de experimentación. Todas las cifras salen de correr el código en el modo sim; cada sección dice cómo reproducirla. Para regenerar todo y comparar byte a byte con lo commiteado: `python experiments/parada_tecnica/generar_todo.py --verificar`.

Pedido de la dirección: (1) correr un caso que genere una teoría y mostrar punto a punto el ciclo de vida; (2a) cooperación, colaboración y transferencia a un agente novato; (2b) ranking y recuperación de la teoría propia; (3) equipos DAG que maduran a otro equipo; (4) la traza de cada etapa de cada rol; (5) las métricas de equidad en la utilidad de cada rol.

## Punto 1 · Una teoría generada y el ciclo de vida punto a punto

- **Qué se demuestra (mecanismo, en el entorno simulado):** un caso genera una teoría ⟨Si, A, Sf, P, K, U⟩ en la región 5 del primer ciclo, y el agente recorre las siete regiones del LLC en cada ciclo (Ierache 2010, §4.2, pp. 61–64). El estado se gana con la regla de evolución (Fig. 4.28, p. 123, adaptada a un agente) y el gate de Ω.
- **Comando:** `python experiments/parada_tecnica/p1_teoria_punto_a_punto.py --version v2` (y `--version v1`).
- **Números clave (v2):** la teoría T1 nace en el ciclo 1 (Si: skills_match = 0, exp_band = senior, edu = Licenciatura, seniority_ok = True; A = ADVANCE; Sf: calificado = False; P 1, K 1, U 0,333). El agente termina en **Mature** en 100 ciclos: Born → Novice en el ciclo 20; Novice → Trained en el ciclo 80; Trained → Mature en el ciclo 100. Al final: 40 teorías, 77 ciclos exitosos, 34 «azares»; ΣP = K en todas las celdas: sí.
- **Figuras y trazas:** `docs/parada_tecnica/v2/p1_linea_de_tiempo.png`, `docs/parada_tecnica/v2/p1_traza_ciclo1.md`, `docs/parada_tecnica/p1_gate_caracteristica.png`.
- **Rótulos:** «Ilustrativo, entorno simulado (modo sim); no es evidencia experimental» · «Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección».
- **Resultados inesperados:** con la v1 el agente quedó en **Born** tras 60 ciclos: el gate puntual de Ω con ventanas de 20 era ruido de muestreo y la U binaria trababa la elección (`docs/parada_tecnica/E2_v1_vs_v2.md`).
- **Historial:** v1 (pre-registro `2d847ad`) → v2 (pre-registro `231715a`, E2_RESPUESTA): Ω niega solo con evidencia de sesgo (LCB), U basada en la acción (U(Si, A) con Laplace) y evaluación acumulada en la capa. Las dos corridas quedan lado a lado.

## Punto 2a · Cooperación, colaboración y transferencia a un agente novato

- **Qué se demuestra (mecanismo):** la colaboración de un agente en un estado superior a uno inferior (Alg. 4.10, p. 116) y la cooperación entre pares del mismo estado (Alg. 4.9, p. 109), con los axiomas de §4.3.1 (pp. 69–70), el invariante ΣP = K y la procedencia PROV-O (`prov:wasDerivedFrom`).
- **Comandos:** `python experiments/parada_tecnica/p2a_compartir.py` y `python experiments/parada_tecnica/p2a_cooperacion_a9.py`.
- **Números clave:** colaboración A (Mature) → B (Novice): aceptada, 13 iguales, 4 similares, 23 nuevas. Cooperación B ↔ C (los dos Novice) con A9 en decisiones: aceptada (10/3/3 de B en C y 10/1/1 de C en B); base común a los dos: sí; ΣP = K en los dos: sí. Contraejemplos rechazados por los axiomas: 2 de 2.
- **La teoría fallida también sirve:** T* (Si: skills_match = 0, exp_band = senior, edu = Licenciatura, seniority_ok = True; A = ADVANCE; Sf: calificado = False) llega a B con P 2, K 2, U 0,250; en esa celda el planificador de B elige REJECT (T14), no T*: la experiencia de fracaso que transfiere A evita que el novato repita el error.
- **Archivos:** `docs/parada_tecnica/v2/p2a_compartir.md`, `docs/parada_tecnica/v2/p2a_procedencia.ttl`, `docs/parada_tecnica/E3_cooperacion_A9_lado_a_lado.md`.
- **Rótulos:** «Ilustrativo, entorno simulado (modo sim); no es evidencia experimental» · «Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección».
- **Resultados inesperados:** con A9 en ventanas la cooperación B ↔ C se rechazó (rechazada por el código: el par SemanticMatcher_B no puede aportar sin historia de equidad (A9: requiere ≥3 ventanas, tiene 2)).
- **Historial:** A9 en ventanas (E3) → A9 en decisiones (pre-registro corto `cf8d0b0`, E3_RESPUESTA): al menos 20 decisiones propias y los dos grupos. Motivo: con el gate por LCB la cantidad de decisiones ya entra en la cota; en el LLC se coopera entre SAR recién nacidos (p. 124).

## Punto 2b · Ranking y recuperación de la teoría propia

- **Qué se demuestra (mecanismo):** el planificador del LLC ordena las teorías de la celda por U desc, P desc y K asc (Fig. 4.21, p. 107) y la primera, si es un plan válido, decide la acción; sin teoría aplicable recurre al «azar» (Fig. 4.17, pp. 101–102), que acá es probar la acción todavía no probada o el operador BIO (DE-3).
- **Comando:** `python experiments/parada_tecnica/p2b_planificador.py --version v2`.
- **Números clave:** (i) misma Si que T*: candidatas 1. T23 REJECT (U 0,857, P 5, K 5); 2. T1 ADVANCE (U 0,333, P 1, K 1); elige REJECT (celda). (ii) Si nueva con similitud máxima 0,75: con respaldo por similitud, REJECT (similitud); sin respaldo, REJECT (azar_bio). (iii) nada aplicable: REJECT (azar_bio).
- **Archivos:** `docs/parada_tecnica/v2/p2b_planificador.md`.
- **Rótulos:** «Ilustrativo, entorno simulado (modo sim); no es evidencia experimental» · «Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección».
- **Resultados inesperados:** la Fig. 4.21 y el Alg. 4.7 (p. 108) eligieron teorías distintas 0 veces en P1 v2 y 0 en P1 v1 (se informa para la decisión 2).
- **Historial:** el mismo de P1 (v1 → v2).

## Punto 3 · Equipos DAG: un equipo maduro hace madurar a otro

- **Qué se demuestra (mecanismo):** equipos DAG orquestados con LangGraph (Parser → Semantic Matcher → Bias Auditor → Orchestrator → Explainer); el equipo A colabora rol por rol con el equipo B al nacer; B0 es el control con los mismos casos; BC coopera con C en Novice; N es el SAR neutro de L-3.
- **Comandos:** `python experiments/parada_tecnica/p3_equipos_dag.py` y `python experiments/parada_tecnica/p3_descriptivas.py`.
- **Números clave:** ciclo en que cada rol gana su estado, B · B0 (en los roles por caso, casos procesados), y ciclos exitosos B · B0:

| Rol | Novice | Trained | Mature | Ciclos exitosos |
|---|---|---|---|---|
| Parser | 20 · 20 | 40 · 40 | 60 · 60 | 241 · 238 |
| Semantic Matcher | 40 · 20 | 80 · 40 | 100 · — | 204 · 173 |
| Explainer | 20 · 20 | 40 · 40 | 60 · 60 | 260 · 255 |

  Casos resueltos de punta a punta: B 190, B0 158, neutro 21 (de 260). En BIO, la regla se cumple sin interrupción desde el ciclo 5 en el Parser de B (11 en B0) y 4 en el Explainer (19 en B0). L-3 literal entre configuraciones (B evaluada): Parser %CEA 97,5 ≥ %RCE 71,9, %TNA 100,0 ≤ %RTN 100,0: evoluciona; Semantic Matcher %CEA 30,8 ≥ %RCE 13,1, %TNA 85,5 ≤ %RTN 90,0: evoluciona; Explainer %CEA 602,7 ≥ %RCE 447,3, %TNA 100,0 ≤ %RTN 100,0: evoluciona.
- **Nota técnica sobre L-3, para conversar con Jorge.** Con estas definiciones, %TNA ≤ %RTN equivale a «promedio de teorías nuevas ≤ máximo», y %CEA ≥ %RCE, a «ciclos exitosos de la configuración evaluada ≥ promedio de las configuraciones». Parser y Explainer: %TNA = %RTN porque B no generó teorías propias (las recibió todas de A); la condición se cumple por igualdad. El %CEA del Explainer (602,7) es tan alto porque el operador BIO neutro casi nunca completa la explicación: el Explainer de N tuvo 37 ciclos exitosos de 260.
- **Cuánto pesa el entorno.** Las magnitudes dependen del entorno pre-registrado: los operadores BIO son imperfectos por construcción, y el equipo neutro resuelve 21 de 260 casos. Los resultados muestran el mecanismo de colaboración y maduración, no cuánto ayudaría en un sistema real.
- **Figuras:** `docs/parada_tecnica/p3_maduracion_equipos.png`, `docs/parada_tecnica/p3_curvas_aprendizaje.png`.
- **Rótulos:** «Ilustrativo, entorno simulado (modo sim); no es evidencia experimental» · «Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección».
- **Resultados inesperados:** el Matcher de B gana Novice y Trained más tarde que el de B0 (su Parser, con las teorías de A, sube el punto de comparación), pero solo él llega a Mature; Parser y Explainer promueven en el primer cierre posible en todos los equipos (piso de 20 ciclos por estado); el Matcher de C no sale de Born, así que no coopera (axioma [a]); la semilla de E4 es poco frecuente (`e4_muestreo_calificados.md`).
- **Historial:** desde E5, por E4_RESPUESTA: el Bias Auditor no tiene estados ganados, solo el Explainer explora en WIO y la Si del Explainer es tipo · destinatario. Las métricas descriptivas (frente al neutro y curvas sin piso) se agregaron por E5_RESPUESTA sobre las mismas corridas.

## Punto 4 · La traza de cada etapa de cada rol

- **Qué se demuestra (mecanismo):** para cada rol del equipo y cada caso, la situación inicial, las candidatas y la acción, la situación final, P, K y U, la región en que se registró la teoría y el estado del agente; todo en RDF con PROV-O, verificado con SHACL (ΣP = K, DE-4) y consultable con SPARQL.
- **Comando:** `python experiments/parada_tecnica/p4_traza.py`.
- **Números clave:** 54211 tripletas (Teoria 109, CicloLLC 793, RegionLLC 5551, Decision 260, LecturaEquidad 1040); SHACL conforma: sí; las dos pruebas negativas fallan como deben: sí. Estados ganados: Parser Mature, Semantic Matcher Trained, Explainer Mature; Bias Auditor: Born en E4; desde E5 no tiene estados por diseño (su regla es regulatoria; decisión 1 de E4_RESPUESTA).
- **Archivos:** `docs/parada_tecnica/p4_traza_BIO-041.html`, `docs/parada_tecnica/p4_traza_TBO-081.html`, `docs/parada_tecnica/p4_traza_WIO-081.html`, `docs/parada_tecnica/p4_equipo.ttl`, `p4_shacl.txt`, `p4_sparql.md`.
- **Rótulos:** «Ilustrativo, entorno simulado (modo sim); no es evidencia experimental» · «Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección».
- **Resultados inesperados:** el contrafáctico CE_0 se corrigió antes de la corrida oficial (Parser y Explainer); el Explainer llegó a Mature con una celda que nunca resolvió (48 fracasos en WIO), lo que motivó la decisión 3 de E4_RESPUESTA; el Bias Auditor no puede promover con la regla de P1 (su acción la decide la regla).
- **Historial:** E4 queda como está; las reglas de E5 valen desde E5.

## Punto 5 · Métricas de equidad en la utilidad de cada rol

- **Qué se demuestra (mecanismo):** una métrica de equidad por rol, calculada en el plano de auditoría (el grupo nunca entra en Si, A ni los prompts); U_rol = α·U + (1 − α)·ê en la utilidad; y, con un sesgo programado por un proxy, cuándo las reglas del Monitor de Equidad pueden actuar y cuándo no. Documento para la dirección: `docs/parada_tecnica/METRICAS_EQUIDAD_POR_ROL.md`.
- **Comandos:** `python experiments/parada_tecnica/p5_metricas_equidad.py`, `python experiments/parada_tecnica/p5_equidad_v2.py`, `python experiments/parada_tecnica/p5_control_post_hoc.py` y `python experiments/parada_tecnica/metricas_equidad_doc.py`.
- **Números clave:** en los 600 casos, Parser brecha de completitud 0,003 (d_TV del canal proxy 0,144); Matcher odds igualadas 0,149 y paridad demográfica 0,123 (diferencia de calificados 0,103); Explainer 0,017; Bias Auditor Δ_esc 0,000. Tres criterios que no coinciden (casos de E4): paridad demográfica 0,154, aciertos 0,761 y 0,746, TPR 0,825 y 0,667.
- **U_rol con α = 0,5:** v1 (ê por teoría) cambió la teoría 175 veces y la acción 0; v2 (ê por celda) se aplicó en 404 planificaciones, no se pudo aplicar por falta de evidencia en 1354, y cambió la teoría 0 y la acción 0 veces.
- **Sesgo programado** («parámetros programados»; brecha del operador 0,40): la regla de ventana de 20 no deriva nunca; la regla acumulada deriva al neutro desde W07 (24 ventanas); el Matcher que aprende baja la paridad demográfica de 0,437 a 0,160 y ninguna regla lo detecta; Ω acepta su compartición. Atenuación: ilustra el mecanismo; no es evidencia de la conjetura de atenuación.
- **Qué significa que α = 0,5 no haya cambiado nada.** El ajuste funciona: el test `tests/test_bloquee_e6_v2.py::test_la_equidad_por_celda_puede_cambiar_la_accion` muestra que, con evidencia en las dos acciones y U parecidas, α = 0,5 cambia la acción. El ajuste por equidad necesita evidencia sobre la acción que el agente no elige, y el aprendizaje deja de generarla (en 1354 de 1758 planificaciones faltó evidencia). Es una propiedad del tamaño de muestra y de la explotación, no de la definición.
- **Control post hoc** («control agregado después de ver los resultados; no pre-registrado»): Matcher sin rasgo ni sesgo, paridad demográfica 0,080, odds igualadas 0,069, estado final Mature. La diferencia con el Matcher sesgado que aprende (0,160 frente a 0,080) da una idea del sesgo residual atribuible al proxy, del orden de 0,08, con la salvedad de que el control no es un contrafáctico limpio: llegó a Mature y no explora en WIO.
- **Figura:** `docs/parada_tecnica/p5_sesgo_programado.png`.
- **Rótulos:** «Ilustrativo, entorno simulado (modo sim); no es evidencia experimental» · «Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección».
- **Resultados inesperados:** α = 0,5 no cambió ninguna acción ni en la v1 ni en la v2; paridad de aciertos pareja no implica odds igualadas; el gate de compartición dejó pasar al Matcher sesgado (la brecha estaba por debajo de lo detectable); ê casi no ve el sesgo por proxy (pocas lecturas de AR en las celdas sin título local).
- **Historial:** E6 (pre-registro `9e346e0`, ê por teoría) → E6 v2 (pre-registro corto `9431eb8`, E6_RESPUESTA): ê por celda (Si, A), y sin evidencia en alguna candidata α = 1 para todas. Motivo: con U(Si, A) la v1 solo reordenaba variantes de la misma acción y su respaldo premiaba la falta de evidencia.

## Preguntas para el encuentro

1. **Decisión 1 de la hoja.** ¿La evolución y la compartición se condicionan a la ausencia de evidencia de sesgo (lo implementado: LCB > τ_b niega) o a la evidencia de equidad?
2. **A9.** ¿La historia mínima para donar (extensión nuestra, no del LLC) se mide en decisiones (lo implementado desde E3) o en ventanas?
3. **Ω sin ciclo de vida.** ¿El Monitor de Equidad debe tener un ciclo de vida propio? La propuesta es que no: su regla es regulatoria (BIO) y no se aprende.
4. **Con qué se compara un agente dentro de un equipo.** ¿Contra sus propias entradas (lo que aprendió él; lo implementado para la promoción) o contra el equipo neutro (su aporte al resultado conjunto)?
5. **Criterio del rol decisor.** ¿Qué criterio de equidad fija la dirección para el Matcher? La propuesta es odds igualadas a nivel rol.
6. **Sesgo por proxy por debajo de lo detectable.** ¿Reportar el d_TV como alerta, exigir más historia antes de compartir o aceptar el límite?
7. **Observación selectiva en WIO.** En WIO la Sf la da la revisión humana de todos los casos; en producción solo se observa el resultado de los que avanzan. ¿Se modela?
8. **Si, A y Sf por rol.** ¿Se aceptan las definiciones de la sección 6 del handoff tal como quedaron corridas (con la Si del Explainer sin «motivos» desde E5)?
9. **%RCE, %RTN, n y α.** ¿Se aceptan los valores fijados antes de correr (%RCE 25, %RTN 20, intervalos de 20 ciclos, α = 1,0 y 0,5)? En la tesis, los porcentajes se determinan comparando configuraciones de SAR (Anexo L-3, Tablas L-16 y L-17).
10. **Semántica LLC de P y K (decisión 2).** ¿Se adopta el registro de la Fig. 4.13 con ΣP = K (implementado como opción) frente a la semántica anterior?
11. **Similitud como extensión del planificador.** ¿Se acepta el respaldo por similitud (solo con la celda vacía, registrado) como extensión declarada para situaciones en lenguaje natural?
12. **Equidad en la utilidad con poca evidencia.** Con m_min = 5 lecturas por grupo, el ajuste casi nunca se aplica, porque el agente deja de probar la acción que no elige. ¿Se exige exploración mínima para estimar la equidad de ambas acciones, se baja m_min o se acepta el límite?

## Estado

Rama `eje1/bloque-e`, revisada por Claude chat (`docs/parada_tecnica/E7_REVISION_ClaudeChat_2026-10-08.md`); sin merge a `main`, que queda congelada hasta después del encuentro con la dirección. Los puntos de control de cada fase y las respuestas de Claude chat están en `docs/parada_tecnica/` (E0 a E7). No se adoptó ninguna de las decisiones de la hoja: están implementadas como opciones para que la dirección las evalúe funcionando.

**Infraestructura.** La orquestación con LangGraph existió desde la primera versión (06/06/2026) y quedó fuera del historial al reorganizarlo; E1 la restituye (`core/grafo.py`); el código de junio queda en la rama `rescate/langgraph-junio`.

