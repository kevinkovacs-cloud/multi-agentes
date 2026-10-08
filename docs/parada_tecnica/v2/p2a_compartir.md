# P2a · Cooperación, colaboración y transferencia (pre-registro v2)

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

## Agentes (estados ganados)

| Equipo | Agente | Estado | Ciclos | Teorías | Ventanas | Promociones |
|---|---|---|---|---|---|---|
| A | SemanticMatcher | Mature | 100 | 40 | 5 | ciclo 20: Born → Novice; ciclo 80: Novice → Trained; ciclo 100: Trained → Mature |
| B | SemanticMatcher_B | Novice | 40 | 16 | 2 | ciclo 40: Born → Novice |
| C | SemanticMatcher_C | Novice | 20 | 12 | 1 | ciclo 20: Born → Novice |

## Operaciones

### 1. Colaboración A → B (transferencia a un agente novato)

- **Estados:** donante Mature, receptor Novice.
- **Ω sobre SemanticMatcher:** can_donate = True (5 ventanas); brecha 0,100, LCB 0,000 frente a τ_b = 0,075 → sin evidencia de sesgo; r informada 0,780.
- **Resultado:** aceptada — axiomas, can_donate y Ω sin evidencia de sesgo.
- **Base del receptor:** 16 → 43 teorías; igual 13 · similar 4 · nueva 23; ΣP = K en el receptor: se cumple.

| Teoría del donante (Si · A · Sf) | Entra como | En el donante (P, K, U) | En el receptor antes | En el receptor después |
|---|---|---|---|---|
| {"edu": "Licenciatura", "exp_band": "senior", "seniority_ok": true, "skills_match": 0} · ADVANCE · {"calificado": false} | igual | 1, 1, 0,333 | 1, 1, 0,333 | 2, 2, 0,250 |
| {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 3} · ADVANCE · {"calificado": false} | igual | 1, 1, 0,333 | 2, 4, 0,500 | 3, 5, 0,429 |
| {"edu": "Licenciatura", "exp_band": "senior", "seniority_ok": true, "skills_match": 3} · ADVANCE · {"calificado": true} | igual | 8, 9, 0,818 | 3, 4, 0,667 | 11, 13, 0,800 |
| {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 1} · ADVANCE · {"calificado": false} | igual | 1, 1, 0,333 | 2, 3, 0,400 | 3, 4, 0,333 |
| {"edu": "Licenciatura", "exp_band": "senior", "seniority_ok": true, "skills_match": 1} · ADVANCE · {"calificado": true} | igual | 5, 5, 0,857 | 7, 7, 0,889 | 12, 12, 0,929 |
| {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 3} · REJECT · {"calificado": false} | nueva | 6, 6, 0,875 | — | 6, 6, 0,875 |
| {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 1} · REJECT · {"calificado": true} | similar | 1, 7, 0,778 | — | 1, 8, 0,800 |
| {"edu": "Licenciatura", "exp_band": "senior", "seniority_ok": true, "skills_match": 2} · ADVANCE · {"calificado": true} | igual | 7, 8, 0,800 | 9, 9, 0,909 | 16, 17, 0,895 |
| {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 1} · REJECT · {"calificado": false} | igual | 6, 7, 0,778 | 1, 1, 0,667 | 7, 8, 0,800 |
| {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 2} · ADVANCE · {"calificado": false} | igual | 1, 1, 0,333 | 1, 1, 0,333 | 2, 2, 0,250 |
| {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 0} · ADVANCE · {"calificado": true} | similar | 1, 3, 0,400 | — | 1, 4, 0,333 |
| {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 0} · ADVANCE · {"calificado": false} | igual | 2, 3, 0,400 | 1, 1, 0,333 | 3, 4, 0,333 |
| {"edu": "Maestría", "exp_band": "senior", "seniority_ok": true, "skills_match": 2} · ADVANCE · {"calificado": false} | nueva | 1, 1, 0,333 | — | 1, 1, 0,333 |
| {"edu": "Maestría", "exp_band": "junior", "seniority_ok": false, "skills_match": 0} · ADVANCE · {"calificado": false} | nueva | 1, 1, 0,333 | — | 1, 1, 0,333 |
| {"edu": "Maestría", "exp_band": "junior", "seniority_ok": false, "skills_match": 3} · ADVANCE · {"calificado": true} | nueva | 1, 3, 0,400 | — | 1, 3, 0,400 |
| {"edu": "Licenciatura", "exp_band": "senior", "seniority_ok": true, "skills_match": 2} · ADVANCE · {"calificado": false} | similar | 1, 8, 0,800 | — | 1, 17, 0,895 |
| {"edu": "Maestría", "exp_band": "senior", "seniority_ok": true, "skills_match": 0} · ADVANCE · {"calificado": false} | nueva | 1, 1, 0,333 | — | 1, 1, 0,333 |
| {"edu": "Maestría", "exp_band": "junior", "seniority_ok": false, "skills_match": 3} · ADVANCE · {"calificado": false} | nueva | 2, 3, 0,400 | — | 2, 3, 0,400 |
| {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 0} · REJECT · {"calificado": false} | igual | 5, 6, 0,750 | 4, 4, 0,833 | 9, 10, 0,833 |
| {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 2} · REJECT · {"calificado": false} | igual | 5, 5, 0,857 | 2, 2, 0,750 | 7, 7, 0,889 |
| {"edu": "Maestría", "exp_band": "junior", "seniority_ok": false, "skills_match": 3} · REJECT · {"calificado": false} | nueva | 6, 6, 0,875 | — | 6, 6, 0,875 |
| {"edu": "Maestría", "exp_band": "senior", "seniority_ok": true, "skills_match": 3} · ADVANCE · {"calificado": false} | nueva | 2, 5, 0,571 | — | 2, 5, 0,571 |
| {"edu": "Licenciatura", "exp_band": "senior", "seniority_ok": true, "skills_match": 0} · REJECT · {"calificado": false} | igual | 5, 5, 0,857 | 1, 3, 0,400 | 6, 8, 0,700 |
| {"edu": "Maestría", "exp_band": "junior", "seniority_ok": false, "skills_match": 0} · REJECT · {"calificado": false} | nueva | 4, 4, 0,833 | — | 4, 4, 0,833 |
| {"edu": "Maestría", "exp_band": "junior", "seniority_ok": false, "skills_match": 1} · ADVANCE · {"calificado": false} | nueva | 1, 1, 0,333 | — | 1, 1, 0,333 |
| {"edu": "Maestría", "exp_band": "senior", "seniority_ok": true, "skills_match": 3} · REJECT · {"calificado": true} | nueva | 1, 1, 0,333 | — | 1, 1, 0,333 |
| {"edu": "Maestría", "exp_band": "senior", "seniority_ok": true, "skills_match": 3} · ADVANCE · {"calificado": true} | nueva | 3, 5, 0,571 | — | 3, 5, 0,571 |
| {"edu": "Maestría", "exp_band": "senior", "seniority_ok": true, "skills_match": 0} · REJECT · {"calificado": false} | nueva | 4, 4, 0,833 | — | 4, 4, 0,833 |
| {"edu": "Maestría", "exp_band": "junior", "seniority_ok": false, "skills_match": 2} · ADVANCE · {"calificado": false} | nueva | 1, 1, 0,333 | — | 1, 1, 0,333 |
| {"edu": "Maestría", "exp_band": "senior", "seniority_ok": true, "skills_match": 1} · ADVANCE · {"calificado": true} | nueva | 2, 2, 0,750 | — | 2, 2, 0,750 |
| {"edu": "Maestría", "exp_band": "senior", "seniority_ok": true, "skills_match": 2} · REJECT · {"calificado": false} | nueva | 1, 2, 0,500 | — | 1, 2, 0,500 |
| {"edu": "Maestría", "exp_band": "senior", "seniority_ok": true, "skills_match": 2} · REJECT · {"calificado": true} | nueva | 1, 2, 0,500 | — | 1, 2, 0,500 |
| {"edu": "Maestría", "exp_band": "junior", "seniority_ok": false, "skills_match": 2} · REJECT · {"calificado": false} | nueva | 2, 2, 0,750 | — | 2, 2, 0,750 |
| {"edu": "Maestría", "exp_band": "junior", "seniority_ok": false, "skills_match": 1} · REJECT · {"calificado": false} | nueva | 2, 2, 0,750 | — | 2, 2, 0,750 |
| {"edu": "Doctorado", "exp_band": "senior", "seniority_ok": true, "skills_match": 1} · REJECT · {"calificado": true} | nueva | 1, 1, 0,333 | — | 1, 1, 0,333 |
| {"edu": "Doctorado", "exp_band": "junior", "seniority_ok": false, "skills_match": 3} · ADVANCE · {"calificado": false} | nueva | 1, 1, 0,333 | — | 1, 1, 0,333 |
| {"edu": "Doctorado", "exp_band": "junior", "seniority_ok": false, "skills_match": 1} · REJECT · {"calificado": false} | nueva | 2, 2, 0,750 | — | 2, 2, 0,750 |
| {"edu": "Licenciatura", "exp_band": "senior", "seniority_ok": true, "skills_match": 3} · ADVANCE · {"calificado": false} | igual | 1, 9, 0,818 | 1, 4, 0,667 | 2, 13, 0,800 |
| {"edu": "Doctorado", "exp_band": "junior", "seniority_ok": false, "skills_match": 0} · REJECT · {"calificado": false} | nueva | 2, 2, 0,750 | — | 2, 2, 0,750 |
| {"edu": "Licenciatura", "exp_band": "junior", "seniority_ok": false, "skills_match": 0} · REJECT · {"calificado": true} | similar | 1, 6, 0,750 | — | 1, 10, 0,833 |

### 2. Cooperación B ↔ C

- **Estados:** donante Novice, receptor Novice.
- **Ω sobre SemanticMatcher_B:** can_donate = False (2 ventanas); brecha 0,000, LCB 0,000 frente a τ_b = 0,075 → sin evidencia de sesgo; r informada 1,000.
- **Ω sobre SemanticMatcher_C:** can_donate = False (1 ventana); brecha 0,100, LCB 0,000 frente a τ_b = 0,075 → sin evidencia de sesgo; r informada 0,900.
- **Resultado:** rechazada — rechazada por el código: el par SemanticMatcher_B no puede aportar sin historia de equidad (A9: requiere ≥3 ventanas, tiene 2).

### 3a. Contraejemplo: cooperación A ↔ B

- **Estados:** donante Mature, receptor Novice.
- **Ω sobre SemanticMatcher:** can_donate = True (5 ventanas); brecha 0,100, LCB 0,000 frente a τ_b = 0,075 → sin evidencia de sesgo; r informada 0,780.
- **Ω sobre SemanticMatcher_B:** can_donate = False (2 ventanas); brecha 0,000, LCB 0,000 frente a τ_b = 0,075 → sin evidencia de sesgo; r informada 1,000.
- **Resultado:** rechazada — rechazada por el código: la cooperación requiere mismo estado de evolución (Def. 7). Axioma: §4.3.1 [a] (p. 70): la cooperación se realiza solo entre SARs que se encuentran con el mismo estado de evolución.

### 3b. Contraejemplo: colaboración B → A

- **Estados:** donante Novice, receptor Mature.
- **Ω sobre SemanticMatcher_B:** can_donate = False (2 ventanas); brecha 0,000, LCB 0,000 frente a τ_b = 0,075 → sin evidencia de sesgo; r informada 1,000.
- **Resultado:** rechazada — rechazada por el código: el colaborador debe tener nivel estrictamente superior (Def. 8). Axioma: §4.3.1 [b] (p. 70): la colaboración se presenta entre un SAR en un estado de evolución superior y un SAR receptor en un estado inferior.

## T\* y T\*✓ en el receptor (después de la colaboración A → B)

### T\*: {"edu": "Licenciatura", "exp_band": "senior", "seniority_ok": true, "skills_match": 0} · ADVANCE · {"calificado": false}

- **En A (donante):** P = 1, K = 1, U = 0,333.
- **En B (receptor):** P = 2, K = 2, U = 0,250.
- **Procedencia:** `https://moav-hr.diit.unlam.edu.ar/ontology/Teoria/SemanticMatcher_B/3e30cf25cc66c1f1` prov:wasDerivedFrom `https://moav-hr.diit.unlam.edu.ar/ontology/Teoria/SemanticMatcher/3e30cf25cc66c1f1`.
- **Planificador de B** (capa TBO) ante un caso con esa Si: elige REJECT (celda, T14); ¿es esta teoría? **no**.

### T\*✓: {"edu": "Licenciatura", "exp_band": "senior", "seniority_ok": true, "skills_match": 3} · ADVANCE · {"calificado": true}

- **En A (donante):** P = 8, K = 9, U = 0,818; supera U = 0,75 en el ciclo 5 de P1.
- **En B (receptor):** P = 11, K = 13, U = 0,800.
- **Procedencia:** `https://moav-hr.diit.unlam.edu.ar/ontology/Teoria/SemanticMatcher_B/aeca6e6faefa0c69` prov:wasDerivedFrom `https://moav-hr.diit.unlam.edu.ar/ontology/Teoria/SemanticMatcher/aeca6e6faefa0c69`.
- **Planificador de B** (capa TBO) ante un caso con esa Si: elige ADVANCE (celda, T4); ¿es esta teoría? **sí**.

## Consulta SPARQL de la cadena de procedencia

```sparql
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX moacv: <https://moav-hr.diit.unlam.edu.ar/ontology/>
SELECT ?receptor ?donante WHERE { ?receptor prov:wasDerivedFrom ?donante ;
                                           moacv:clave ?c . FILTER(?c = ?clave) }
```

- **T\*:** https://moav-hr.diit.unlam.edu.ar/ontology/Teoria/SemanticMatcher_B/3e30cf25cc66c1f1 ← https://moav-hr.diit.unlam.edu.ar/ontology/Teoria/SemanticMatcher/3e30cf25cc66c1f1.
- **T\*✓:** https://moav-hr.diit.unlam.edu.ar/ontology/Teoria/SemanticMatcher_B/aeca6e6faefa0c69 ← https://moav-hr.diit.unlam.edu.ar/ontology/Teoria/SemanticMatcher/aeca6e6faefa0c69.
