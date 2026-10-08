# P2b · Ranking y recuperación de la teoría propia

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

**Agente:** el de P1 al terminar su corrida: estado Born, capa BIO, 19 teorías, 60 ciclos.

**T\*:** T1 · Si {"edu": "Licenciatura", "exp_band": "senior", "seniority_ok": true, "skills_match": 0} · A = ADVANCE · Sf = {"calificado": false} · P = 1, K = 1, U = 0,00.

## (i) Un caso con la misma Si que T*

| Puesto | Teoría | A | Sf | u_tarea | U para ordenar | P | K |
|---|---|---|---|---|---|---|---|
| 1 | T14 | REJECT | {"calificado": false} | 1,00 | 1,000 | 2 | 3 |
| 2 | T1 | ADVANCE | {"calificado": false} | 0,00 | 0,000 | 1 | 1 |
| 3 | T18 | REJECT | {"calificado": true} | 0,00 | 0,000 | 1 | 3 |

**Elegida (α = 1):** REJECT (T14). Por qué: es la primera del orden (U, P, K) en la celda y su u_tarea > 0.
Regla de validez aplicada: no. Desacuerdo Fig. 4.21 / Alg. 4.7: no.

**E(t) de cada candidata** (plano de auditoría; decisiones en las que fue el plan): T1: sin usos como plan; T14: {"no-AR": {"aciertos": 1, "usos": 2}}; T18: sin usos como plan.

**α = 0,5:** elige REJECT (T14); ¿cambia la elegida? **no**. Ninguna candidata tiene ê(t) estimable con m_min = 5 usos por grupo: se usa α = 1 y queda registrado.

## (ii) Un caso con una Si nueva: respaldo por similitud (extensión declarada)

Si {"edu": "Licenciatura", "exp_band": "mid", "seniority_ok": true, "skills_match": 0} (celda vacía; similitud máxima con una teoría de u_tarea > 0 = 0,750; δ = 0,7).

| Puesto | Teoría | A | Sf | u_tarea | U para ordenar | P | K | Similitud |
|---|---|---|---|---|---|---|---|---|
| 1 | T14 | REJECT | {"calificado": false} | 1,00 | 1,000 | 2 | 3 | 0,750 |

**Elegida con el respaldo activado:** REJECT (T14). Por qué: la celda está vacía y es la primera, en el orden (U, P, K), entre las teorías con similitud ≥ δ y u_tarea > 0 (extensión declarada).
**Como en P1 (respaldo desactivado):** ADVANCE — no hay plan válido: «azar» del planificador, primera acción no probada en la celda (orden fijo).

## (iii) Un caso sin nada aplicable

Si {"edu": "Maestría", "exp_band": "mid", "seniority_ok": true, "skills_match": 0} (celda vacía; similitud máxima 0,500 < δ; acción del operador BIO = REJECT).

- **En la capa del agente (BIO):** ADVANCE — no hay plan válido: «azar» del planificador, primera acción no probada en la celda (orden fijo); cuenta como azar: sí.
- **Si el agente estuviera en WIO:** REJECT — no hay plan válido: «azar» del planificador con el operador BIO; cuenta como azar: sí.

## α = 1 frente a α = 0,5 en todas las celdas de la base

Celdas: 8; con ê(t) estimable en alguna candidata (m_min = 5 usos por grupo): 0; celdas donde α = 0,5 cambia la elegida: **0**.

