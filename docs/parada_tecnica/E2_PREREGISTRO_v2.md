# E2 · Pre-registro v2 (antes de correr P1 v2, P2b v2 y E3)

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

Única revisión, decidida por Claude chat con delegación de Kevin (`docs/parada_tecnica/E2_RESPUESTA_ClaudeChat_2026-10-08.md`). La v1 sigue en `configs/parada_tecnica_v1.yaml` y su corrida queda en el informe como resultado pre-registrado.

## Cambios y motivos

1. **Gate de Ω para la evolución.** Ω niega la promoción solo si hay evidencia de sesgo: LCB_δ/L(|Δ_DP|) > τ_b = 0,075 sobre todas las decisiones del agente en la capa, con δ = 0,05 y L = cierres posibles de la capa (Bonferroni). La reputación r y el certificado se informan pero no deciden. Motivo: con ventanas de 20 el gate puntual era ruido de muestreo; es el mismo primitivo que la regla de bloqueo publicada.
2. **U basada en la acción.** U(Si, A) = (aciertos de A en la celda + 1)/(K(Si, A) + 2), igual para todas las variantes (Si, A, ·); los aciertos son la suma de los P de las variantes cuya Sf hace correcta la acción. P y K siguen la Fig. 4.13 y ΣP = K se mantiene. Orden de la Fig. 4.21 literal sobre (U, P, K). Validez del plan: U ≥ 0,5. Rango [0, 1] (en la tesis, [−1, 1]). Motivo: §4.4.3.2 (pp. 89–90), p. 107 y la recomendación 2(a) de la hoja.
3. **Evaluación acumulada en la capa.** CE_a, CE_0 y las teorías nuevas se acumulan desde el inicio de la capa hasta cada cierre; %TN = teorías nuevas / ciclos en la capa. Motivo: p. 118 y Fig. 4.28.
4. **Compartición (E3).** Se rechaza al donante si hay evidencia de sesgo en sus decisiones (LCB_δ > τ_b) o si no cumple `can_donate` (≥ 3 ventanas). Equipos: A = 20261008, B = 20261108, C = 20261208. Solo estados ganados: si falta uno, se frena y se avisa.

**Sin cambios:** semilla, n, ciclos por capa, %RCE, %RTN, umbral de ciclo exitoso, ε de WIO, τ_b y δ. Ciclo exitoso: la acción del ciclo fue correcta, igual para el agente y para el SAR neutro.

## Característica del gate v2 (`p1_gate_caracteristica.png`)

Brecha de paridad mínima (|p̂_a − p̂_b|, con n decisiones por grupo acumuladas en la capa) que hace negar la promoción. «—» = con ese n ninguna brecha alcanza.

| n por grupo | L = 3 | L = 5 |
|---|---|---|
| 10 | — | — |
| 20 | 0,850 | 0,850 |
| 30 | 0,700 | 0,733 |
| 40 | 0,600 | 0,625 |
| 50 | 0,560 | 0,580 |
| 75 | 0,467 | 0,480 |
| 100 | 0,410 | 0,430 |
| 150 | 0,347 | 0,360 |
| 200 | 0,310 | 0,320 |

Con decenas de decisiones por capa, Ω solo puede frenar ante evidencia de un sesgo grande; certificar equidad en positivo exige historias largas (m_min = 47 ventanas).
