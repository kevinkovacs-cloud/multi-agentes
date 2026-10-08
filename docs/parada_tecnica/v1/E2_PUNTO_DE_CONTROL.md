# E2 · Punto de control del Bloque E, pre-registro v1 (puntos 1 y 2b del pedido)

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

Rama `eje1/bloque-e`, sin push. Decisiones aplicadas: `docs/parada_tecnica/E0_RESPUESTA_P1-P5_ClaudeChat_2026-10-08.md`. Parámetros y entorno pre-registrados antes de la primera corrida (`configs/parada_tecnica.yaml`, `docs/parada_tecnica/E2_PREREGISTRO_ENTORNO.md`).

## Qué se hizo

- **E1:** orquestación del DAG con LangGraph (`core/grafo.py`), equivalente al orquestador secuencial en el lote de la PoC.
- **E2:** registro de teorías del LLC (Fig. 4.13, ΣP = K), planificador por ranking (Fig. 4.21, validez del plan, «azar» sin decisiones aleatorias), motor de las 7 regiones dentro del agente, estadísticas de la región 6, estado ganado y regla de evolución de P1 ∧ gate de Ω, entorno BIO/TBO/WIO y rol Matcher.

## Cómo reproducirlo

```bash
python experiments/parada_tecnica/preregistro.py
python experiments/parada_tecnica/p1_teoria_punto_a_punto.py --version v1
python experiments/parada_tecnica/p2b_planificador.py --version v1
python experiments/parada_tecnica/informe_e2.py --version v1
```

## P1 · El ciclo de vida punto a punto

- **Resultado:** estado final **Born** tras 60 ciclos; capas recorridas: BIO (60 ciclos, sin promoción).
- **Traza región por región del ciclo 1:** `docs/parada_tecnica/v1/p1_traza_ciclo1.md`. T* = T1 (`https://moav-hr.diit.unlam.edu.ar/ontology/Teoria/SemanticMatcher/3e30cf25cc66c1f1`), nace en R5 con P = 1, K = 1, U = 0,00.
- **Línea de tiempo:** `docs/parada_tecnica/v1/p1_linea_de_tiempo.png`.

### Evaluaciones de la región 7 (al cierre de cada intervalo)

CE_a y CE_0 del intervalo.

| Capa | Ciclo | CE_a | CE_0 | %CEA (≥ %RCE) | %TN (≤ %RTN) | fair(W) | r | Gate Ω puntual | LCB de la capa (v2) | Ω decide | Certificado (informado) | Promueve | Estado después |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BIO | 20 | 14 | 11 | 27,3 % (sí) | no aplica | 0,70 | 0,700 | rechaza | — | niega | rechaza | no | Born |
| BIO | 40 | 17 | 9 | 88,9 % (sí) | no aplica | 0,70 | 0,700 | rechaza | — | niega | rechaza | no | Born |
| BIO | 60 | 12 | 13 | -7,7 % (no) | no aplica | 0,90 | 0,767 | rechaza | — | niega | rechaza | no | Born |

%RCE = 25, %RTN = 20, τ = 0,8, n = 20.

### Planificador

- **Regla de validez del plan aplicada:** 5 veces (ciclos 8, 10, 12, 22, 28).
- **Desacuerdos Fig. 4.21 / Alg. 4.7:** 0.
- **Decisiones por motivo:** azar: primera acción no probada: 12; plan de la celda (Fig. 4.21): 47; azar: operador BIO: 1.
- **Invariante ΣP = K en la base final:** se cumple.

### Estadísticas de la región 6 al final

Situaciones 8 · teorías acumuladas 19 · teorías exitosas 8 · ciclos exitosos 43 de 60 · planes 47 (exitosos 35) · azares 13 · teorías por intervalo de U [0, 0, 0, 8] · P/K general 0,632.

## P2b · Ranking y recuperación de la teoría propia

Detalle: `docs/parada_tecnica/v1/p2b_planificador.md`.

- **(i) misma Si que T\*:** elige REJECT (T14, plan de la celda (Fig. 4.21)); con α = 0,5 no cambia.
- **(ii) Si nueva:** con el respaldo activado, respaldo por similitud (extensión) → REJECT; como en P1, azar: primera acción no probada → ADVANCE.
- **(iii) nada aplicable:** en BIO, azar: primera acción no probada → ADVANCE; en WIO, azar: operador BIO → REJECT.
- **α = 0,5 en toda la base:** 0 de 8 celdas con ê(t) estimable (m_min = 5 por grupo); cambia la elegida en 0.

## Resultados que no fueron los esperados (se reportan tal cual)

1. **El agente no sale de Born.** Ningún cierre de intervalo cumplió la regla (ciclo 20: falla gate de Ω; ciclo 40: falla gate de Ω; ciclo 60: falla %CEA, gate de Ω). Con la regla «sin promoción → detener», TBO y WIO no se recorren en P1; las transiciones del motor están verificadas en `tests/test_bloquee_ciclo.py`.
2. **El gate de Ω frena la promoción con ventanas chicas.** ciclo 20: %CEA = 27,3 % cumple, pero r = 0,700 < τ; fair(W) = 0,70. Sin ninguna disparidad real, con 10 casos por grupo y tasa de avance 0,65, una brecha de al menos 3/10 ocurre con probabilidad 0,239; ciclo 40: %CEA = 88,9 % cumple, pero r = 0,700 < τ; fair(W) = 0,70. Sin ninguna disparidad real, con 10 casos por grupo y tasa de avance 0,65, una brecha de al menos 3/10 ocurre con probabilidad 0,239. Es el ruido de muestreo de ventanas de 20 casos: el gate puntual no distingue disparidad real de azar a ese tamaño.
3. **Bloqueo por U binaria en el orden de la Fig. 4.21.** Si {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 0}: el plan repitió ADVANCE con 0 aciertos y 6 fracasos; la otra acción nunca se probó. Una sola observación favorable deja la variante (Si, A, Sf) con U = 1, y como U es la primera clave del orden, queda primera aunque la acción fracase después; la regla de validez solo actúa si la primera del orden tiene u_tarea = 0.
4. **El agente acierta menos que el SAR neutro en algún intervalo:** ciclo 60 (CE_a = 12, CE_0 = 13).
5. **α = 0,5 no se pudo evaluar:** ninguna teoría juntó 5 usos como plan en cada grupo, así que U_rol cae en α = 1 en todas las celdas.
6. **T\* nace de un fracaso** (u_tarea del ciclo 1 = 0; U al nacer = 0,000): en el ciclo 1 la celda estaba vacía, el agente exploró la primera acción del orden fijo y no era la correcta. Es la teoría que E3 tiene que compartir.

## Para decidir antes de seguir (no se cambió nada: son reglas pre-registradas)

*Decidido después por Claude chat en `E2_RESPUESTA_ClaudeChat_2026-10-08.md` → pre-registro v2.*

- **Gate de Ω y tamaño de ventana.** Con n = 20 la reputación queda dominada por el ruido de muestreo. Opciones: mantenerlo y reportarlo; evaluar el gate sobre más ventanas o ventanas más grandes; o exigir el gate solo cuando la ventana tiene el tamaño de detección (`stats.n_power`).
- **U binaria por variante.** Opciones: mantener el orden literal de la Fig. 4.21 y reportar el bloqueo; extender la regla de validez (por ejemplo, plan válido solo si la acción no acumula más fracasos que aciertos en la celda); o calcular u_tarea sobre (Si, A), como el método de utilidad basado en la acción de la tesis, que compara la acción de la teoría con la del robot reactivo en esa situación (§4.4.3.2, pp. 89–90).
- **m_min por grupo para ê(t).** Con 60 ciclos no se alcanza; α = 0,5 no tiene efecto en esta escala.

Cualquier cambio va en un commit nuevo, con su motivo, y se reporta en el informe final (regla de P1).
