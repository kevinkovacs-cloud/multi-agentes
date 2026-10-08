# E2 · P1 y P2b: pre-registro v1 frente a v2

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

La v1 es el resultado pre-registrado original (`configs/parada_tecnica_v1.yaml`); la v2, la única revisión (`E2_PREREGISTRO_v2.md`). Misma semilla y mismo entorno.

| | v1 | v2 |
|---|---|---|
| Reglas | gate puntual; U u_tarea; evaluación por_intervalo | gate evidencia_de_sesgo; U accion; evaluación acumulada_en_la_capa |
| Estado final | Born | Mature |
| Ciclos | 60 | 100 |
| Capas (ciclos) | BIO (60) | BIO (20), TBO (60), WIO (20) |
| Promociones | ninguna | ciclo 20: Born → Novice; ciclo 80: Novice → Trained; ciclo 100: Trained → Mature |
| Cierres en que Ω negó | 3 | 0 |
| Teorías acumuladas | 19 | 40 |
| Ciclos exitosos | 43 de 60 | 77 de 100 |
| Azares | 13 | 34 |
| Regla de validez aplicada | 5 | 14 |
| Desacuerdos Fig. 4.21 / Alg. 4.7 | 0 | 0 |
| Celdas bloqueadas (plan con más fracasos que aciertos) | 1 | 0 |
| ΣP = K | se cumple | se cumple |
| T* (al final) | T1 ADVANCE · P = 1, K = 1, U = 0,000 | T1 ADVANCE · P = 1, K = 1, U = 0,333 |
| P2b (i) celda de T* | REJECT (T14, plan de la celda (Fig. 4.21)) | REJECT (T23, plan de la celda (Fig. 4.21)) |
| P2b (ii) Si nueva, con respaldo | respaldo por similitud (extensión) → REJECT | respaldo por similitud (extensión) → REJECT |
| P2b (iii) nada aplicable | BIO: azar: primera acción no probada → ADVANCE | WIO: azar: operador BIO → REJECT |
| α = 0,5 cambia la elegida | 0 de 8 celdas | 0 de 20 celdas |

Detalle: `docs/parada_tecnica/v1/E2_PUNTO_DE_CONTROL.md` y `docs/parada_tecnica/v2/E2_PUNTO_DE_CONTROL.md`.
