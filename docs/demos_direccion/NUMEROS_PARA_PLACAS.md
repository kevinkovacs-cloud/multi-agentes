# Números para las placas — Bloque D (demos para la dirección)

Generado por `experiments/demos_direccion/generar_todo.py`: **ningún número está escrito a mano**; todo sale de correr los demos (JSON y figuras en `docs/demos_direccion/`). Decimales con coma, como en las figuras; los JSON usan punto.

Todas las salidas llevan dos rótulos: *ilustrativo, modo sim; no es evidencia experimental* y *semántica actual del código; puede cambiar con las decisiones 2 y 5 de la dirección*.

Regenerar:

```bash
python experiments/demos_direccion/generar_todo.py
```

## D1 · Selección de teoría por embeddings (P3)

- δ que rige en el Matcher: **0,7** (el default de `TheoryRetriever` es 0,6, pero el Matcher hereda 0,7 de `MOACVAgent`).
- Teorías que superan δ con la Si de Fátima: token-cosine **3 de 11**; embeddings **11 de 11** (coseno entre 0,898 y 1,000).
- Seleccionada: token-cosine **T1**, embeddings **T1** → misma teoría: **sí**; top-3 recuperadas iguales: **no** ([1, 9, 3] vs [1, 11, 10]).
- La teoría con la misma Si que la consulta (T3, coseno 1) queda en el puesto **3** (token-cosine) y **10** (embeddings) del orden de `retrieve`.
- Modelo: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dimensiones); PCA 2D explica 63,2 % de la varianza.
- Figura: `docs/demos_direccion/d1_espacio_embeddings.png` · `docs/demos_direccion/d1_similitud_barras.png`.
- Leyenda: *la similitud (coseno) solo decide qué teorías pasan δ; entre las que pasan, la seleccionada sale de la clave (U, P, K, recencia, id).* PCA es una proyección: la selección usa el coseno en la dimensión completa.
- Rótulo: *ilustrativo, modo sim; no es evidencia experimental*.
- Rótulo: *semántica actual del código; puede cambiar con las decisiones 2 y 5 de la dirección*.

## D2 · Creación e iteración de una teoría en dos tareas (P1)

- Teorías nuevas por tarea (región 7): tarea 1 = **11**, tarea 2 = **1** (decrece).
- Teoría seguida: **T1** (ADVANCE; Si: skills=2 · mid · Lic · sen=sí), la teoría que el Matcher selecciona (★) para decidir el caso de Fátima en la tarea 1.
- Nace en la tarea 1, caso de Ana García: P = 1, K = 1, U = 0,667. Tras 3 usos: P = 3, K = 3, U = **0,800**; puesto en su celda: 1/1.
- Fue la seleccionada (★) para decidir **6** casos.
- Aciertos del Matcher: tarea 1 = 12/12, tarea 2 = 10/12; casos que refuerzan una teoría existente: 1 y 11.
- Figura: `docs/demos_direccion/d2_evolucion_PKU.png`.
- Leyenda: *la teoría nace en la región 5 con el primer caso y cada caso equivalente la refuerza (P, K, U); en la segunda tarea nacen menos teorías nuevas (1 vs 11).*
- Rótulo: *ilustrativo, modo sim; no es evidencia experimental*.
- Rótulo: *semántica actual del código; puede cambiar con las decisiones 2 y 5 de la dirección*.

## D3 · Transferencia maestro → aprendiz del mismo rol (P2)

- Donante A (Matcher de la PoC, Trained): r = **0,833** ≥ τ = 0,8 con 3 ventanas → transferencia **aceptada**.
- Teorías de A en B: igual **8** · similar **0** · nueva **3**; base de B: 9 → **12** teorías.
- Contraejemplo r < τ: donante C con r = **0,633** (6 ventanas) → **rechazada**.
- Contraejemplo sin historia: A∅ con 0 ventanas → can_donate = False → **rechazada** (hacen falta 3); `approve_sharing` sola daría True por el prior r0.
- Estado de B: Born → Born (la transferencia no cambia el estado).
- Figura: `docs/demos_direccion/d3_transferencia.png`.
- Leyenda: *Ω habilita la transferencia solo si el donante tiene historia (≥ m0 ventanas) y reputación r ≥ τ; las teorías entran por las reglas del Alg. 4.10.*
- Rótulo: *ilustrativo, modo sim; no es evidencia experimental*.
- Rótulo: *semántica actual del código; puede cambiar con las decisiones 2 y 5 de la dirección*.

## D4 · Maduración sobre el caso y segunda tarea (P4)

- Gate puntual (τ = 0,8): W1: Born → Novice · W2: Novice → Trained · W3: Trained → Mature.
- Gate certificado: queda en **Born** tras 6 ventanas; aun con ventanas perfectas necesita **m_min(1,0) = 47** (δ = 0,05). Es la propiedad del certificado, no un defecto.
- Media de fair(W) en las 6 ventanas: 0,694.
- Tarea 2: **12/12** casos recuperan una teoría con aciertos (tarea 1: 8/12); aciertos 10/12; teorías nuevas **1** (tarea 1: 11).
- Eventos de la región 7 en el trail: puntual 3, certificado 6.
- Figura: `docs/demos_direccion/d4_linea_de_tiempo.png`.
- Leyenda: *con el gate puntual el Matcher llega a Mature en la tarea 1 y en la tarea 2 reutiliza sus teorías; el certificado exige una historia mucho más larga (m_min(1,0) = 47 ventanas).*
- Rótulo: *ilustrativo, modo sim; no es evidencia experimental*.
- Rótulo: *semántica actual del código; puede cambiar con las decisiones 2 y 5 de la dirección*.

## D5 · Diversidad en comité con sesgos programados (I5)

- D(M) = (1 − ρ̄)/2: (a) homogéneo **0,004** · (b) diverso **0,622** · (c) diverso con piso **0,473**; d_max(3) = 0,75.
- |Δ_DP| del comité vs. media de los miembros: (a) homogéneo 0,395 vs 0,397 (**1,00**) · (b) diverso 0,080 vs 0,238 (**0,34**) · (c) diverso con piso 0,320 vs 0,297 (**1,08**).
- |Δ_DP| de cada miembro: (a) homogéneo [0,400, 0,390, 0,400] · (b) diverso [0,360, 0,265, 0,090] · (c) diverso con piso [0,545, 0,030, 0,315].
- Δ_DP de la calificación real en la muestra: 0,095 (400 candidatos).
- Figura: `docs/demos_direccion/d5_diversidad.png`.
- Leyenda: *con sesgos de grupo en direcciones distintas el promedio del comité cancela parte del sesgo de sus miembros (comité/media = 0,34); con un piso común, el comité queda en 0,320 frente a 0,080 sin piso.*
- Rótulo: *ilustrativo, modo sim; no es evidencia experimental*.
- Rótulo: *semántica actual del código; puede cambiar con las decisiones 2 y 5 de la dirección*.
- Rótulo obligatorio: *parámetros programados: ilustra el mecanismo de la condición C2 (diversidad); no es evidencia de la conjetura de atenuación*.

## Resultados que no fueron los esperados (se reportan tal cual)

- D1: con embeddings sobre la Si serializada en JSON **todas** las teorías superan δ = 0,7 (coseno ≥ 0,898); el umbral no discrimina y el top-k lo decide la clave (U, P, K, recencia, id): entran teorías poco parecidas ([1, 11, 10]).
- D1: la teoría con la misma Si que la consulta (T3) no es la seleccionada en ningún backend: la similitud solo filtra, no ordena.
- D2: la celda de Si de T1 tiene una sola teoría en todo el recorrido, así que su puesto es siempre 1 de 1 (no hay competencia que mostrar).
- D2: la teoría seleccionada cambió la acción del Matcher (contrafáctico: score sin teoría) en 2 caso(s): caso 10 (tarea 1, T1 ADVANCE: REJECT → ADVANCE, acierto), caso 110 (tarea 2, T10 REJECT: ADVANCE → REJECT, error). Corrige 1, empeora 1.
- D2: errores del Matcher que no dependen de la teoría (el score base ya estaba del otro lado del umbral): caso 105 (tarea 2).
- D3: no hay teorías **similares** (0): ninguna teoría de A comparte celda (Si, A) con una teoría de B que tenga otro Sf: en estos lotes, la misma Si con la misma acción tuvo siempre el mismo resultado. La regla existe en `sharing._merge` pero estos lotes no la ejercitan.
- D3: la transferencia no cambia el estado de madurez de B (sigue en Born): el estado se deriva de TBO/WIO, no del tamaño de la base.
- D4: en W6 la reputación puntual cae por debajo de τ y el agente sigue en Mature: `advance` solo avanza (el ciclo del código es monótono, no hay regresión).
- D4: el estado de madurez no cambia las decisiones del Matcher en modo sim (mismas acciones con el gate puntual y con el certificado).
- D4: las ventanas son de 4 casos; fair(W) toma valores extremos (p. ej. 0,00 en W6).
- D5: en (c) diverso con piso la disparidad del comité (0,320) supera la media de sus miembros (0,297): el piso común no se cancela y el miembro menos sesgado queda en 0,030, lo que baja la media; frente al peor miembro la relación es 0,59.
- D5: la calificación real ya tiene Δ_DP = 0,095 en la muestra (misma distribución por grupo, pero muestra finita): es la referencia de la figura.
