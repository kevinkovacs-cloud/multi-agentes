# ESTADO del PoC — hecho vs. trabajo futuro

Documento honesto del alcance, para ser preciso en la reunión. Separa lo que el PoC
**demuestra hoy** (viabilidad del pipeline y de la ontología) de lo que es **investigación
de la tesis** (Ejes 1–3). La fuente de verdad del modelo es el plan de tesis.

## ✅ Hecho y demostrable (corre y está testeado — 25 tests en verde)

**Pipeline y ciclo de vida**
- Pipeline de 5 agentes end-to-end con un comando (`run_poc.py`, `demo_caso.py`). (§4.1)
- Teorías ⟨Si,A,Sf,P,K,U⟩: selección por ranking U>P>K (Def. 4), equivalencia por cuantización (Def. 3).
- Compartición: cooperación (Def. 7) y colaboración maestro→aprendiz (Def. 8), con gating por reputación r/τ (Def. 9).
- Monitor de Utilidad de Equidad Ω: `fair(W)`, bloqueo/escalado por umbral, regiones 4 y 7. (§2.4)
- Integración teorías↔LLM: recuperación por similitud + few-shot, punto de inyección explícito. (§2.2)

**Ontología y trazabilidad (interoperabilidad RDF)**
- TBox §2.5 (clases/propiedades/axiomas) + alineación PROV-O.
- ABox generado automáticamente desde el estado y los spans de OpenTelemetry.
- Validación SHACL conforme + consulta SPARQL de ejemplo (auditoría de sesgo).
- **Orden de trazabilidad tras round-trip (obs. Becerra):** el orden de ejecución se ancla a un ordinal explícito (`moacv:ordenEjecucion`) + encadenado `prov:wasInformedBy`, y se recupera con `ORDER BY` tras serializar→parsear. No depende del orden de tripletas ni del timestamp (que puede colisionar). Test: `tests/test_orden_trazabilidad.py`.
- **Explicabilidad derivada de la serialización (obs. Becerra):** `core/ontology/explain.explain_from_rdf` reconstruye la explicación desde el grafo RDF (no del estado en memoria) y la articula para dos destinatarios —regulador (completitud/umbrales/cumplimiento) y usuario (lenguaje llano)—. Test: `tests/test_xai_rdf.py`. *Alcance: derivación + destinatarios; no es XAI por atribución (SHAP/LIME).*

**Ingeniería**
- Decoupling `core/` (genérico) vs `instances/hr/` (dominio), verificado por test.
- Parser robusto (CVs mal formateados, sinónimos, texto/HTML) + guardrail BIO de no-retención.
- Caso de demostración §5 determinístico (basal rechaza → modelo escala). 
- Corre con modelos locales (Llama 3.1 8B vía Ollama) o en modo `sim` sin LLM. Sin claves.
- App web standalone (5 vistas) para el video. `MAPPING.md` (código↔documento).

**Instrumental listo (interfaces, sin correr experimentos)**
- `μ(M)=b(M)/b_in` (Def. 10), diversidad `D(M)` (Def. 11), harness de fidelidad (intervención causal).

## 🔬 Trabajo futuro (tesis — NO incluido en el PoC, no fabricado)

- **Eje 1 (teórico):** demostrar/­refutar la conjetura de atenuación μ<1 bajo C1/C2/C3; teoremas de composición. *(El PoC mide μ pero NO la valida — riesgo alto declarado en el plan.)*
- **Eje 2 (experimental):** benchmark sintético en español; experimentos de amplificación/atenuación en topologías; LLMs calibrados (fine-tuning/RLHF, capa TBO — hoy los scores `llm` están sin calibrar).
- **Eje 3 (validación):** medición sistemática de fidelidad de teorías; validación de utilidad del audit trail con usuarios reales (n≥30).
- Embeddings reales para la similitud de teorías (hoy proxy cosine sobre tokens clave=valor).
- Persistencia del audit trail en backend (OpenTelemetry/Langfuse/Grafana en vivo); hoy es en memoria + export RDF.
- **Triple store persistente:** hoy la trazabilidad es serialización RDF a Turtle (grafo `rdflib` en memoria), **no** un store persistente. El round-trip serializar→recuperar está testeado; montar un triple store real (p. ej. Fuseki/GraphDB) es trabajo futuro. *(Precisión pedida por Becerra: no llamar "triple store" a la serialización.)*

## Cómo verificarlo
```bash
python scripts/check_env.py        # entorno + Ollama + smoke (pipeline + ontología SHACL)
python -m pytest tests/ -q         # 25 tests
python experiments/demo_caso.py    # caso §5 determinístico
python experiments/run_poc.py      # pipeline completo + fairness + RDF + fidelidad
```
