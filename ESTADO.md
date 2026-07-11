# ESTADO del PoC — hecho vs. trabajo futuro

Documento honesto del alcance, para ser preciso en la reunión. Separa lo que el PoC
**demuestra hoy** (viabilidad del pipeline y de la ontología) de lo que es **investigación
de la tesis** (Ejes 1–3). La fuente de verdad del modelo es el plan de tesis.

> **La sección "✅ Hecho" describe `main`** (lo que sale el video). La branch
> `eje1/formalizacion-v2` la extiende — ver la sección propia al final.

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

## Cómo verificarlo (main)
```bash
python scripts/check_env.py        # entorno + Ollama + smoke (pipeline + ontología SHACL)
python -m pytest tests/ -q         # 35 tests (main)
python experiments/demo_caso.py    # caso §5 determinístico
python experiments/run_poc.py      # pipeline completo + fairness + RDF + fidelidad
```

---

## Branch `eje1/formalizacion-v2` — formalización v2 e instrumento experimental

Implementa las correcciones de la **auditoría matemática** (A1–A11/B1–B8) y la
infraestructura que los Ejes 1–2 necesitan. **NO fabrica ni valida resultados; μ<1 sigue
siendo hipótesis.** Un commit atómico por ítem; **`main` intacto** (el video sale de main).

**Correcciones formales al core (Tier A):**
- **A1** equivalencia por cuantización (`q_canonical`/`q_grid`): relación de equivalencia REAL (transitiva) → la fusión de bases es asociativa; separada de la recuperación por similitud.
- **A2** confiabilidad con Laplace `(P+1)/(K+2)`; **A5+A10** desempate determinista (recencia, id).
- **A7** equalized odds con ΔTPR y ΔFPR; **A3+N2** `D=(1−ρ̄)/2` sin clamp + `d_max(k)`; **B3** disparidad firmada + detector de inversión.
- **B6+A8** `core/stats.py` + Monitor **certificado** (LCB Hoeffding ⇒ FPR ≤ δ; Def. 12 gate de evolución); **A9** arranque en frío (prior r0, `can_donate`); **N3** reputación por agente; **N1** μ→μ_rel + interfaz b_in.

**Instrumento experimental (Tier B) — lo que los Ejes 1–2 no tenían:**
- **B1** auditor experimental **sin oráculo** (`bias_auditor_exp`): estima disparidad por ventana, jamás lee `bias_risk`/`true_qual` ni ajusta scores. La demo con oráculo (video) queda intacta.
- **B2** humano simulado (oracle/noisy/biased) → **μ_auto y μ_total** + tasa de escalamiento.
- **B3** estimador `d_TV` del canal proxy (guardrail BIO auditable); **B4** topologías de **comité** (donde C2/diversidad tiene canal).
- **B5** `e0_instrumento.py` — **GATE**: recupera μ, c_k, ι_k y la cobertura del IC (PASS). **B6** `e_fpr_monitor.py`: FPR puntual 12.2% vs certificado 0.0% ≤ δ.

**Ingeniería (Tier C):** configs YAML + registro de corridas (`runlog`); CI (GitHub Actions) con gate E0; embeddings opcionales (`MOAV_SIMILARITY`); calibración TBO (Platt/isotónica/ECE).

**Tests:** 35 (main) → **~103** (branch). **Deriva numérica de la demo:** ver `DERIVA_DEMO.md`
— las 12 decisiones del lote y el caso Fátima (ESCALATE, ajuste 0.850) se mantienen; cambian
magnitudes (matcher 0.820→0.812, μ_rel 0.703→0.606) por A1 (11 teorías vs 4) y A2.

**Sigue pendiente (no en esta branch):** benchmark es-AR con SCM; empirical-Bernstein
(transcribir constantes de Maurer & Pontil); triple store persistente; embeddings en corrida
real; validación de la conjetura (Eje 1). Decisión al mergear: regrabar el bloque 2 del video
con la corrida nueva, o mantener main congelado hasta la reunión (ver `DERIVA_DEMO.md`).
