# P2b · Ranking y recuperación de la teoría propia (pre-registro v2)

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

**U de la teoría:** basada en la acción, U(Si, A) = (aciertos + 1)/(K + 2); plan válido si U ≥ 0,5.

**Agente:** el de P1 al terminar su corrida: estado Mature, capa WIO, 40 teorías, 100 ciclos.

**T\*:** T1 · Si {"edu": "Licenciatura", "exp_band": "senior", "seniority_ok": true, "skills_match": 0} · A = ADVANCE · Sf = {"calificado": false} · P = 1, K = 1, U = 0,33.

## (i) Un caso con la misma Si que T*

| Puesto | Teoría | A | Sf | U de la teoría | U para ordenar | P | K |
|---|---|---|---|---|---|---|---|
| 1 | T23 | REJECT | {"calificado": false} | 0,86 | 0,857 | 5 | 5 |
| 2 | T1 | ADVANCE | {"calificado": false} | 0,33 | 0,333 | 1 | 1 |

**Elegida (α = 1):** REJECT (T23). Por qué: es la primera del orden (U, P, K) en la celda y es plan válido.
Regla de validez aplicada: no. Desacuerdo Fig. 4.21 / Alg. 4.7: no.

**E(t) de cada candidata** (plano de auditoría; decisiones en las que fue el plan): T1: sin usos como plan; T23: {"AR": {"aciertos": 2, "usos": 2}, "no-AR": {"aciertos": 2, "usos": 2}}.

**α = 0,5:** elige REJECT (T23); ¿cambia la elegida? **no**. Ninguna candidata tiene ê(t) estimable con m_min = 5 usos por grupo: se usa α = 1 y queda registrado.

## (ii) Un caso con una Si nueva: respaldo por similitud (extensión declarada)

Si {"edu": "Licenciatura", "exp_band": "mid", "seniority_ok": true, "skills_match": 0} (celda vacía; similitud máxima con una teoría que es plan válido = 0,750; δ = 0,7).

| Puesto | Teoría | A | Sf | U de la teoría | U para ordenar | P | K | Similitud |
|---|---|---|---|---|---|---|---|---|
| 1 | T23 | REJECT | {"calificado": false} | 0,86 | 0,857 | 5 | 5 | 0,750 |

**Elegida con el respaldo activado:** REJECT (T23). Por qué: la celda está vacía y es la primera, en el orden (U, P, K), entre las teorías con similitud ≥ δ que son plan válido (extensión declarada).
**Como en P1 (respaldo desactivado):** REJECT — no hay plan válido: «azar» del planificador con el operador BIO.

## (iii) Un caso sin nada aplicable

Si {"edu": "Doctorado", "exp_band": "mid", "seniority_ok": true, "skills_match": 0} (celda vacía; similitud máxima 0,500 < δ; acción del operador BIO = REJECT).

- **En la capa del agente (WIO):** REJECT — no hay plan válido: «azar» del planificador con el operador BIO; cuenta como azar: sí.
- **Si el agente estuviera en WIO:** REJECT — no hay plan válido: «azar» del planificador con el operador BIO; cuenta como azar: sí.

## α = 1 frente a α = 0,5 en todas las celdas de la base

Celdas: 20; con ê(t) estimable en alguna candidata (m_min = 5 usos por grupo): 0; celdas donde α = 0,5 cambia la elegida: **0**.

