# E2 · Punto de control del Bloque E, pre-registro v2 (puntos 1 y 2b del pedido)

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

**Pre-registro v2** (`docs/parada_tecnica/E2_PREREGISTRO_v2.md`): gate de Ω por evidencia de sesgo (LCB_δ/L > τ_b sobre la capa), U basada en la acción con validez U ≥ 0,5 y evaluación acumulada en la capa. Es la única revisión.

Rama `eje1/bloque-e`, sin push. Decisiones aplicadas: `docs/parada_tecnica/E0_RESPUESTA_P1-P5_ClaudeChat_2026-10-08.md`. Parámetros y entorno pre-registrados antes de la primera corrida (`configs/parada_tecnica.yaml`, `docs/parada_tecnica/E2_PREREGISTRO_ENTORNO.md`).

## Qué se hizo

- **E1:** orquestación del DAG con LangGraph (`core/grafo.py`), equivalente al orquestador secuencial en el lote de la PoC.
- **E2:** registro de teorías del LLC (Fig. 4.13, ΣP = K), planificador por ranking (Fig. 4.21, validez del plan, «azar» sin decisiones aleatorias), motor de las 7 regiones dentro del agente, estadísticas de la región 6, estado ganado y regla de evolución de P1 ∧ gate de Ω, entorno BIO/TBO/WIO y rol Matcher.

## Cómo reproducirlo

```bash
python experiments/parada_tecnica/preregistro.py
python experiments/parada_tecnica/p1_teoria_punto_a_punto.py --version v2
python experiments/parada_tecnica/p2b_planificador.py --version v2
python experiments/parada_tecnica/informe_e2.py --version v2
```

## P1 · El ciclo de vida punto a punto

- **Resultado:** estado final **Mature** tras 100 ciclos; capas recorridas: BIO (20 ciclos, promovido), TBO (60 ciclos, promovido), WIO (20 ciclos, promovido).
- **Traza región por región del ciclo 1:** `docs/parada_tecnica/v2/p1_traza_ciclo1.md`. T* = T1 (`https://moav-hr.diit.unlam.edu.ar/ontology/Teoria/SemanticMatcher/3e30cf25cc66c1f1`), nace en R5 con P = 1, K = 1, U = 0,33.
- **Línea de tiempo:** `docs/parada_tecnica/v2/p1_linea_de_tiempo.png`.

### Evaluaciones de la región 7 (al cierre de cada intervalo)

CE_a y CE_0 acumulados desde el inicio de la capa.

| Capa | Ciclo | CE_a | CE_0 | %CEA (≥ %RCE) | %TN (≤ %RTN) | fair(W) | r | Gate Ω puntual | LCB de la capa (v2) | Ω decide | Certificado (informado) | Promueve | Estado después |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BIO | 20 | 14 | 11 | 27,3 % (sí) | no aplica | 0,70 | 0,700 | rechaza | 0,000 | aprueba | rechaza | sí | Novice |
| TBO | 40 | 10 | 13 | -23,1 % (no) | no aplica | 0,70 | 0,700 | rechaza | 0,000 | aprueba | rechaza | no | Novice |
| TBO | 60 | 28 | 24 | 16,7 % (no) | no aplica | 0,80 | 0,733 | rechaza | 0,000 | aprueba | rechaza | no | Novice |
| TBO | 80 | 47 | 36 | 30,6 % (sí) | no aplica | 0,80 | 0,750 | rechaza | 0,000 | aprueba | rechaza | sí | Trained |
| WIO | 100 | 16 | 11 | 45,5 % (sí) | no aplica | 0,90 | 0,780 | rechaza | 0,000 | aprueba | rechaza | sí | Mature |

%RCE = 25, %RTN = 20, τ = 0,8, n = 20.

### Planificador

- **Regla de validez del plan aplicada:** 14 veces (ciclos 8, 10, 12, 31, 32, 34, 37, 38, 40, 42, 44, 53, 59, 61).
- **Desacuerdos Fig. 4.21 / Alg. 4.7:** 0.
- **Decisiones por motivo:** azar: primera acción no probada: 28; plan de la celda (Fig. 4.21): 66; azar: operador BIO: 6.
- **Invariante ΣP = K en la base final:** se cumple.

### Estadísticas de la región 6 al final

Situaciones 20 · teorías acumuladas 40 · teorías exitosas 13 · ciclos exitosos 77 de 100 · planes 66 (exitosos 59) · azares 34 · teorías por intervalo de U [0, 18, 9, 13] · P/K general 0,800.

## P2b · Ranking y recuperación de la teoría propia

Detalle: `docs/parada_tecnica/v2/p2b_planificador.md`.

- **(i) misma Si que T\*:** elige REJECT (T23, plan de la celda (Fig. 4.21)); con α = 0,5 no cambia.
- **(ii) Si nueva:** con el respaldo activado, respaldo por similitud (extensión) → REJECT; como en P1, azar: operador BIO → REJECT.
- **(iii) nada aplicable:** en WIO, azar: operador BIO → REJECT; en WIO, azar: operador BIO → REJECT.
- **α = 0,5 en toda la base:** 0 de 20 celdas con ê(t) estimable (m_min = 5 por grupo); cambia la elegida en 0.

## Resultados que no fueron los esperados (se reportan tal cual)

1. **El agente acierta menos que el SAR neutro en algún intervalo:** ciclo 40 (CE_a = 10, CE_0 = 13).
2. **α = 0,5 no se pudo evaluar:** ninguna teoría juntó 5 usos como plan en cada grupo, así que U_rol cae en α = 1 en todas las celdas.
3. **T\* nace de un fracaso** (u_tarea del ciclo 1 = 0; U al nacer = 0,333): en el ciclo 1 la celda estaba vacía, el agente exploró la primera acción del orden fijo y no era la correcta. Es la teoría que E3 tiene que compartir.
4. **El gate de Ω v2 no negó ninguna promoción**: la LCB de |Δ_DP| de la capa quedó en 0,000 en todos los cierres. Es la contracara pre-registrada: con decenas de decisiones por capa, Ω solo puede frenar ante evidencia de un sesgo grande (`p1_gate_caracteristica.png`); certificar equidad en positivo exige historias largas (m_min = 47 ventanas).
5. **La reputación informada queda por debajo de τ en 5 de 5 cierres** (r = 0,700, 0,700, 0,733, 0,750, 0,780): en esos cierres, el gate puntual de la v1 habría negado.

## Estado de la revisión

Es la única revisión (E2_RESPUESTA §4): no se cambia nada más. Las preguntas abiertas (promoción por ausencia de evidencia de sesgo o por evidencia de equidad; validez del plan; m_min) van al encuentro con la dirección.
