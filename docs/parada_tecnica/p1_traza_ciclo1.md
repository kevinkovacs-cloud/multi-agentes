# P1 · Traza región por región del ciclo 1

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

**Agente:** SemanticMatcher (rol matcher) · **estado:** Born · **capa:** BIO · **caso:** Caso BIO-001 (id 10000).

| Región | Qué hace el LLC (Ierache 2010, §4.2) | Valores en este ciclo |
|---|---|---|
| R1 (R1_situacion_inicial) | Situación inicial: se percibe y normaliza la situación (Si). | caso = {"edu": "Licenciatura", "exp": 10, "id": 10000, "nombre": "Caso BIO-001", "skills": ["Java", "React", "SQL"]}; si = {"edu": "Licenciatura", "exp_band": "senior", "seniority_ok": true, "skills_match": 0} |
| R2 (R2_accion) | Acción: el planificador por ranking (Fig. 4.21) elige el plan; sin plan válido, «azar». | accion = ADVANCE; motivo = azar_no_probada; es_azar = True; teoria_plan = None; candidatas = []; validez_aplicada = False; desacuerdo_alg47 = None; accion_bio = REJECT |
| R3 (R3_situacion_final) | Situación final: el entorno responde después de la acción (Sf). | sf = {"calificado": false}; fuente = etiqueta del escenario de entrenamiento |
| R4 (R4_utilidad) | Utilidad: u_tarea de la acción para el resultado observado. | u_tarea = 0.0; alpha = 1.0 |
| R5 (R5_aprendizaje) | Aprendizaje: registro de la teoría y ponderación de P y K (Fig. 4.13). | teoria = 1; registro = nueva; p = 1; k = 1; u = 0.0; clave = ["{\"edu\": \"Licenciatura\", \"exp_band\": \"senior\", \"seniority_ok\": true, \"skills_match\": 0}", "ADVANCE", "{\"calificado\": false}"] |
| R6 (R6_estadisticas) | Estadísticas de aprendizaje (§4.4.9). | ciclos = 1; situaciones = 1; teorias_acumuladas = 1; teorias_por_intervalo_u = [0, 0, 0, 0]; teorias_exitosas = 0; teorias_nuevas = 1; ciclos_exitosos = 0; planes = 0; planes_exitosos = 0; azares = 1; pk_por_intervalo_u = [null, null, null, null]; pk_general = 1.0 |
| R7 (R7_evolucion) | Evolución: se evalúa al cierre de cada intervalo (Fig. 4.28 ∧ gate de Ω). | evaluada = False; proxima_evaluacion = 20 |

## La teoría T* que nace en la región 5

- **IRI:** `https://moav-hr.diit.unlam.edu.ar/ontology/Teoria/SemanticMatcher/3e30cf25cc66c1f1`
- **Clave:** `["{\"edu\": \"Licenciatura\", \"exp_band\": \"senior\", \"seniority_ok\": true, \"skills_match\": 0}", "ADVANCE", "{\"calificado\": false}"]`
- **Al nacer (ciclo 1):** P = 1, K = 1, U = 0,00
- **Al final de la corrida:** P = 1, K = 1, U = 0,00
