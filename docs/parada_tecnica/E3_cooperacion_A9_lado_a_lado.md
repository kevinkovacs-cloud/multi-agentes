# E3 · Cooperación B ↔ C: A9 en ventanas frente a A9 en decisiones

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

| | Original (A9 en ventanas) | Pre-registro corto (A9 en decisiones) |
|---|---|---|
| Resultado | rechazada | aceptada |
| Motivo | rechazada por el código: el par SemanticMatcher_B no puede aportar sin historia de equidad (A9: requiere ≥3 ventanas, tiene 2) | axiomas, can_donate y Ω sin evidencia de sesgo |
| Ω sobre B (brecha, LCB) | 0,000, 0,000 → sin evidencia de sesgo | 0,000, 0,000 → sin evidencia de sesgo |
| Ω sobre C (brecha, LCB) | 0,100, 0,000 → sin evidencia de sesgo | 0,100, 0,000 → sin evidencia de sesgo |
| Historia B / C | 2 ventanas, decisiones no evaluadas / 1 ventanas, decisiones no evaluadas | 2 ventanas, 40 decisiones / 1 ventanas, 20 decisiones |
| Igual · similar · nueva (B en C) | — | 10 · 3 · 3 |
| Igual · similar · nueva (C en B) | — | 10 · 1 · 1 |
| Base resultante común (Alg. 4.9) | — | sí |
| ΣP = K en B y en C | — | se cumple |
| Teorías de B antes → después | 16 | 16 → 18 |

## Teorías de B y cómo entran en C (P, K, U)

| Si · A · Sf | Entra como | En B | En C antes | Base común después |
|---|---|---|---|---|
| {"edu": "Licenciatura", "exp_band": "senior", "seniority_ok": true, "skills_match": 1} · ADVANCE · {"calificado": true} | igual | 7, 7, 0,889 | 4, 4, 0,833 | 11, 11, 0,923 |
| {"edu": "Licenciatura", "exp_band": "senior", "seniority_ok": true, "skills_match": 2} · ADVANCE · {"calificado": true} | igual | 9, 9, 0,909 | 2, 2, 0,750 | 11, 11, 0,923 |
| {"edu": "Licenciatura", "exp_band": "senior", "seniority_ok": true, "skills_match": 3} · ADVANCE · {"calificado": true} | igual | 3, 4, 0,667 | 3, 3, 0,800 | 6, 7, 0,778 |
| {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 1} · ADVANCE · {"calificado": true} | nueva | 1, 3, 0,400 | — | 1, 3, 0,400 |
| {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 0} · ADVANCE · {"calificado": false} | igual | 1, 1, 0,333 | 1, 1, 0,333 | 2, 2, 0,250 |
| {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 3} · ADVANCE · {"calificado": true} | similar | 2, 4, 0,500 | — | 2, 5, 0,429 |
| {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 3} · ADVANCE · {"calificado": false} | igual | 2, 4, 0,500 | 1, 1, 0,333 | 3, 5, 0,429 |
| {"edu": "Licenciatura", "exp_band": "senior", "seniority_ok": true, "skills_match": 0} · ADVANCE · {"calificado": false} | igual | 1, 1, 0,333 | 1, 1, 0,333 | 2, 2, 0,250 |
| {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 1} · ADVANCE · {"calificado": false} | nueva | 2, 3, 0,400 | — | 2, 3, 0,400 |
| {"edu": "Licenciatura", "exp_band": "senior", "seniority_ok": true, "skills_match": 0} · REJECT · {"calificado": true} | similar | 2, 3, 0,400 | — | 2, 4, 0,500 |
| {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 0} · REJECT · {"calificado": false} | igual | 4, 4, 0,833 | 1, 1, 0,667 | 5, 5, 0,857 |
| {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 2} · ADVANCE · {"calificado": false} | igual | 1, 1, 0,333 | 1, 1, 0,333 | 2, 2, 0,250 |
| {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 1} · REJECT · {"calificado": false} | nueva | 1, 1, 0,667 | — | 1, 1, 0,667 |
| {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 2} · REJECT · {"calificado": false} | igual | 2, 2, 0,750 | 3, 4, 0,667 | 5, 6, 0,750 |
| {"edu": "Licenciatura", "exp_band": "senior", "seniority_ok": true, "skills_match": 3} · ADVANCE · {"calificado": false} | similar | 1, 4, 0,667 | — | 1, 7, 0,778 |
| {"edu": "Licenciatura", "exp_band": "senior", "seniority_ok": true, "skills_match": 0} · REJECT · {"calificado": false} | igual | 1, 3, 0,400 | 1, 1, 0,667 | 2, 4, 0,500 |
