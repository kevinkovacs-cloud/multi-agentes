# MAPPING — código ↔ propuesta v13

La **v13 es la fuente de verdad**. Esta tabla documenta cómo los nombres y constructos
del documento (§2, §2bis, §2.5, §3, §4) se materializan en el código.

## Estructura (decoupling — P4)
- `src/moav_hr/core/` — modelo **genérico** (§2, §2bis, §3). No importa `instances/` (test: `tests/test_decoupling.py`).
- `src/moav_hr/instances/hr/` — instancia de **selección de personal** (§4).

## Definiciones (§2bis) → código
> Actualizado por la branch `eje1/formalizacion-v2` (correcciones A1–A11/B1–B8 de la auditoría matemática).

| Documento | Código |
|---|---|
| Def. 1 — sistema `M = ⟨G, Θ, Φ, Ω⟩` | `core/orchestrator.Orchestrator` (Φ orden topológico) + `core/monitor.FairnessUtilityMonitor` (Ω) |
| Def. 2 — agente `aᵢ = ⟨θᵢ, sᵢ, Lᵢ⟩` | `core/agent.MOACVAgent` (`theories`, `maturity`, `layer`) |
| Def. 3 — teoría + equivalencia por **cuantización** (A1) | `core/theory.Theory`; identidad por celda `(Q(Si),A[,Q(Sf)])` con `q_canonical` (default, caso simbólico) / `q_grid`; `theories_equal/similar` y `TheoryBase` indexada por celda. La similitud continua (`core/retrieval.similarity`, umbral δ) es SOLO recuperación, no identidad |
| Def. 4 — selección por ranking (U,P,K) + **desempate determinista** (A5+A10) | `core/theory.TheoryBase.select` (orden `-U,-P,K,-recencia,id`; `created_at`/`id` estampados por la base) |
| Def. 5 / 6 — `fair(W)`, `U_op(W)`; **confiabilidad con Laplace** (A2) | `core/fairness.fair_window/acc_window/u_op`; `Theory.reliability = (P+1)/(K+2)` (def. en K=0); `agent.learn` fija `U := reliability` si no se pasa `u` |
| Def. 7 — cooperación (pares) | `core/sharing.cooperate` (**fusión por celdas asociativa**, A1) / `agent.cooperate_with` |
| Def. 8 — colaboración (maestro→aprendiz) | `core/sharing.collaborate`, `agent.transfer_to` (chequeo de nivel + `can_donate`, A9) |
| Def. 9 — reputación `r` / umbral `τ` (**r0, m0, por-agente**) | `agent.reputation(m, r0=0.8)`, `agent.can_donate(m0=3)`, `monitor.approve_sharing`; cada decisor acumula fair(W) sobre sus propias salidas (N3, `run_poc`) |
| Def. 10 — amplificación `μ = b(M)/b_in` | `core/fairness.amplification`; `run_poc` reporta **μ_rel** (vs basal); `bias_in_reference` (b_in del benchmark) declarada para el Eje 2 (N1) |
| Def. 11 — diversidad `D(M) = (1−ρ̄)/2` (A3) | `core/fairness.diversity` (sin clamp) + `d_max(k)=k/(2(k−1))`; se computa SOLO entre miembros de comité (`core/committee`, B4/N2) |
| **Def. 12 — evolución condicionada** (A8) | `monitor.gate_evolution(agent, certified=True)`: promoción de estado solo si `LCB_δ(r̄)` ≥ τ_r |

## Ontología (§2.5) → código
- TBox (clases, propiedades, axiomas, alineación PROV-O): `core/ontology/tbox.py`.
- ABox automático (homomorfismo estado/spans → tripletas): `core/ontology/abox.py`.
- SHACL (validación de conformidad): `core/ontology/shapes.py`.
- SPARQL (interoperabilidad / auditoría de sesgo / orden de ejecución): `core/ontology/queries.py` (incl. `Q_EVENTS_ORDERED`).
- Orden de trazabilidad (§2.5 "orden de ejecución en el grafo"): propiedad ordinal `moacv:ordenEjecucion` + `prov:wasInformedBy` en `core/ontology/abox.py`; round-trip recuperado con `ORDER BY` (test `test_orden_trazabilidad.py`).
- Explicabilidad desde la serialización (§2.5 "trazabilidad ≠ explicabilidad"): `core/ontology/explain.explain_from_rdf` (regulador / usuario, derivada del grafo RDF; test `test_xai_rdf.py`).
- Compartición M2M de teorías (§2.5 "interoperabilidad máquina–máquina"): `core/ontology/sharing_rdf` (`theories_to_turtle` / `theories_from_turtle`) — un agente exporta su base de teorías a RDF y otro la reconstruye desde el grafo, independiente del framework (test `test_m2m_teorias.py`). La ABox completa también es importable (mismo vocabulario §2.5).
- Nombres de clases/propiedades: **idénticos a §2.5** (Agente, AgenteAuditor, Teoria, Situacion(Inicial/Final), Accion, BaseDeConocimiento, Decision, VentanaDeDecisiones, EventoDeAuditoria + subclases, Candidato, AtributoProtegido; poseeBase, contieneTeoria, registra, aplicaEn, esIgualA/esSimilarA, cooperaCon (simétrica), colaboraCon, produce, audita, ponderaComparticion, generaEvento).

## Regiones (§3) → código
Cada evento del audit trail lleva `region=N` (1–7). Región 1 = Parser; 2 = Matcher (RAG+few-shot, §2.2); 4 = Bias Auditor; 7 = decisión/evolución (Orchestrator/Monitor).

## Instrumento experimental (Ejes 1–2 — branch `eje1/formalizacion-v2`)
> El PoC/demo NO se usa para medir: estas piezas son el instrumento científico. La demo (`bias_auditor.py`, oráculo) queda intacta para el video.

- **Certificación estadística** (B6+A8): `core/stats.py` — `hoeffding_halfwidth`, `lcb_abs_diff_rates`, `min_window`, `bootstrap_bca_log_mu`; `empirical_bernstein_halfwidth` es stub (constantes de Maurer & Pontil a transcribir). `monitor.audit_window(certified=True)` bloquea por LCB ⇒ FPR ≤ δ.
- **Auditor sin oráculo** (B1): `instances/hr/bias_auditor_exp.ExperimentalBiasAuditor` — modelo de acceso declarado (`observable_view`, nunca lee `bias_risk`/`true_qual`), estima la disparidad por ventana, no ajusta scores. `HRPipeline(auditor_mode="exp")`.
- **Humano simulado** (B2): `instances/hr/human_sim.resolve` (oracle/noisy/biased) → μ_auto vs μ_total + tasa de escalamiento e.
- **Canal proxy** (B3): `fairness.dtv_lower_bound` — cota inferior de d_TV vía clasificador A-vs-A′ (guardrail BIO auditable).
- **Comités** (B4): `core/committee.Committee` (mean/median/majority); `HRPipeline(topology="committee", k, aggregation)`.
- **E0 / FPR** (B5/B6): `experiments/e0_instrumento.py` (gate: recupera μ, c_k, ι_k, cobertura del IC) y `experiments/e_fpr_monitor.py`.
- **Calibración TBO** (C4): `core/calibration` (Platt/isotónica/ECE — "capa TBO completada" = ECE reportado).
- **Reproducibilidad** (C1): `core/runlog` (config_sha + git_sha → `runs/registry.jsonl`); `configs/*.yaml` + flag `--config`.

## Divergencias declaradas (honestidad)
- **Def. 7 (cooperación) — RESUELTA contra la fuente (03/07/2026):** se verificó el original
  —Ierache (2010), tesis doctoral, SEDICI-UNLP (handle 10915/18378), **Alg. 4.9 (pág. 108)
  y Alg. 4.10 (pág. 115)**, que implementan el método de Maceri & García-Martínez— y el
  código se corrigió para ser fiel: la cooperación **genera una base común (BCCRAB) asignada
  a ambos agentes**; en teorías **similares entra cada variante conservando SU propia P**
  ("P del aportante") con K = suma del par; la colaboración construye la base y la asigna
  **solo al receptor** (BCCRR). El plan (Def. 7) ya coincidía con la fuente. Test:
  `tests/test_sharing_fuente.py`.
- **Def. 8 (plan) — simplificación textual detectada al cotejar la fuente:** el Alg. 4.10
  además **agrega la teoría similar del colaborador** (con su P y K sumado); la redacción
  actual de la Def. 8 ("similar → debilita, suma solo K") describe solo el lado del
  receptor. El código sigue la fuente. Ajuste de redacción del plan = decisión de Kevin
  (menor, no urgente).
- **μ_rel vs μ (Def. 10):** el demo reporta **μ_rel** = b(modelo)/b(basal) (relativo al caso basal). El μ de la Def. 10 se computa contra la **entrada** (b_in del benchmark, `fairness.bias_in_reference`, Eje 2). Ninguno **valida la conjetura μ<1** (Eje 1; el PoC sólo demuestra el mecanismo, §5).
- **empirical-Bernstein pendiente:** el Monitor certifica con **Hoeffding** (válido, conservador). La variante empirical-Bernstein (`core/stats.empirical_bernstein_halfwidth`) es un stub: las constantes exactas se transcriben de Maurer & Pontil (2009), no se inventan.
- **Similitud semántica:** default *cosine* sobre tokens `clave=valor` (sin red). El flag `MOAV_SIMILARITY=embeddings` (extra opcional `.[embeddings]`) activa sentence-transformers y cierra esta divergencia; se mantiene la separación identidad (cuantización) ↔ recuperación (similitud).
- **TBox:** antes era un dict JSON-LD plano; ahora es el esquema RDF de §2.5 con `rdflib`.
- **Ontología "curada manualmente — estado del repositorio" (§2.5):** ahora el TBox es código versionado y el ABox se genera automático.
- **"Triple store" (obs. Becerra):** lo que hay es **serialización RDF a Turtle** sobre un grafo `rdflib` en memoria, no un store persistente. El orden de ejecución NO se confía al orden de tripletas ni al `timestamp` (puede colisionar) sino a un ordinal explícito; el round-trip serializar→recuperar está testeado. Store persistente (Fuseki/GraphDB) = trabajo futuro.
- **Explicabilidad (obs. Becerra):** trazabilidad ≠ explicabilidad. La explicación se deriva del **RDF serializado** (no del estado en memoria) y se separa por destinatario (regulador / usuario). Es derivación + articulación, **no** XAI por atribución (SHAP/LIME/contrafácticos). La explicación tri-nivel L1/L2/L3 del `ExplainabilityAgent` (instancia HR) sigue siendo la del agente; la nueva derivación RDF→explicación es genérica (`core/`).
- **Compartición M2M (obs. Becerra):** hay dos caminos, complementarios. (1) En el pipeline en vivo, la cooperación/colaboración (Def. 7/8, `core/sharing.py`) opera **en memoria** entre agentes del mismo proceso. (2) `core/ontology/sharing_rdf` materializa el intercambio **estándar vía RDF** (M2M, independiente del framework): un agente exporta sus teorías a Turtle y otro las reconstruye desde el grafo. Para soportarlo, el ABox ahora serializa la tupla completa ⟨Si,A,Sf,P,K,U⟩ (antes faltaban la acción A y la situación final Sf).
