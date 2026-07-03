# ESTADO del PoC — hecho vs. trabajo futuro

Documento honesto del alcance, para ser preciso en la reunión. Separa lo que el PoC
**demuestra hoy** (viabilidad del pipeline y de la ontología) de lo que es **investigación
de la tesis** (Ejes 1–3). La fuente de verdad del modelo es el plan de tesis.

## ✅ Hecho y demostrable (corre y está testeado — 35 tests en verde)

**Pipeline y ciclo de vida**
- Pipeline de 5 agentes end-to-end con un comando (`run_poc.py`, `demo_caso.py`). (§4.1)
- Teorías ⟨Si,A,Sf,P,K,U⟩: selección por ranking U>P>K (Def. 4), equivalencia por cuantización (Def. 3).
- Compartición: cooperación (Def. 7) y colaboración maestro→aprendiz (Def. 8), con gating por reputación r/τ (Def. 9).
  **Verificadas contra la fuente** (Ierache 2010, Alg. 4.9/4.10, SEDICI): la cooperación genera base común aplicada por ambos; en similares cada variante conserva su P con K sumado. Test: `tests/test_sharing_fuente.py`.
- Monitor de Utilidad de Equidad Ω: `fair(W)`, bloqueo/escalado por umbral, regiones 4 y 7. (§2.4)
  Cableado y ejercitado en `run_poc.py`: auditoría por ventana (`audit_window`), aprobación de compartición (`approve_sharing`, Def. 9) y gate de evolución (`gate_evolution`, región 7). Tests: `tests/test_monitor.py`.
- Integración teorías↔LLM: recuperación por similitud + few-shot, punto de inyección explícito. (§2.2)

**Ontología y trazabilidad (interoperabilidad RDF)**
- TBox §2.5 (clases/propiedades/axiomas) + alineación PROV-O.
- ABox generado automáticamente desde el estado y los spans de OpenTelemetry.
- Validación SHACL conforme + consulta SPARQL de ejemplo (auditoría de sesgo).
- **Orden de trazabilidad tras round-trip (obs. Becerra):** el orden de ejecución se ancla a un ordinal explícito (`moacv:ordenEjecucion`) + encadenado `prov:wasInformedBy`, y se recupera con `ORDER BY` tras serializar→parsear. No depende del orden de tripletas ni del timestamp (que puede colisionar). Test: `tests/test_orden_trazabilidad.py`.
- **Explicabilidad derivada de la serialización (obs. Becerra):** `core/ontology/explain.explain_from_rdf` reconstruye la explicación desde el grafo RDF (no del estado en memoria) y la articula para dos destinatarios —regulador (completitud/umbrales/cumplimiento) y usuario (lenguaje llano)—. Test: `tests/test_xai_rdf.py`. *Alcance: derivación + destinatarios; no es XAI por atribución (SHAP/LIME).*
- **Compartición M2M de teorías vía ontología (obs. Becerra):** `core/ontology/sharing_rdf` exporta una base de teorías ⟨Si,A,Sf,P,K,U⟩ a RDF/Turtle y otro agente la reconstruye **desde el RDF** (no de objetos en memoria), con el vocabulario estándar de §2.5 — intercambio de conocimiento independiente del framework. Test: `tests/test_m2m_teorias.py`.

**Ingeniería**
- Decoupling `core/` (genérico) vs `instances/hr/` (dominio), verificado por test.
- Parser robusto (CVs mal formateados, sinónimos, texto/HTML) + guardrail BIO de no-retención.
- Caso de demostración §5 determinístico (basal rechaza → modelo escala). 
- Corre con modelos locales (Llama 3.1 8B vía Ollama) o en modo `sim` sin LLM. Sin claves.
- App web standalone (5 vistas) para el video. `MAPPING.md` (código↔documento).

**Instrumental listo (interfaces, sin correr experimentos)**
- `μ(M)=b(M)/b_in` (Def. 10), diversidad `D(M)` (Def. 11), harness de fidelidad (intervención causal).

## ⚠️ Alcance del modo sim (cómo leer los números del demo)

Tres límites del modo `sim`, declarados juntos porque se encadenan:

1. **El sesgo por caso es un proxy etiquetado, no una detección.** El Bias Auditor asigna el
   sesgo según la etiqueta `bias_risk` del dataset sintético (alto=0.10 · medio=0.035 ·
   bajo=0.008); no lo infiere de los datos. La detección per-caso sobre datasets públicos
   (FairCVtest/JobFair) es trabajo del Eje 2.
2. **El ajuste de score usa el oráculo del benchmark.** Al bloquear un caso de alto riesgo,
   `adjusted_score = true_qual` (el ground-truth); en riesgo medio, el ajuste tira 0.4 hacia
   `true_qual`. En producción ese valor no existe: la acción defendible del sistema es
   detectar → bloquear → derivar a revisión humana; el "ajuste" es instrumentación del sim.
3. **Las magnitudes del lote heredan lo anterior.** Las mejoras basal→modelo (subestimación,
   brecha de trato) están parcialmente construidas por esos ajustes con oráculo: demuestran el
   mecanismo (dónde actúa el Monitor), no capacidad de detección ni magnitudes de hallazgo.

Lo que **sí** se computa de verdad en sim, sin etiquetas ni oráculo: la disparidad por ventana
`Δ(W)`/`fair(W)` (Def. 5) sale de las decisiones del lote, y μ/D se calculan con ese
instrumental (sin validar la conjetura).

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
python -m pytest tests/ -q         # 35 tests
python experiments/demo_caso.py    # caso §5 determinístico
python experiments/run_poc.py      # pipeline completo + fairness + RDF + fidelidad
```
