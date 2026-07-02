# MAPPING — código ↔ propuesta v13

La **v13 es la fuente de verdad**. Esta tabla documenta cómo los nombres y constructos
del documento (§2, §2bis, §2.5, §3, §4) se materializan en el código.

## Estructura (decoupling — P4)
- `src/moav_hr/core/` — modelo **genérico** (§2, §2bis, §3). No importa `instances/` (test: `tests/test_decoupling.py`).
- `src/moav_hr/instances/hr/` — instancia de **selección de personal** (§4).

## Definiciones (§2bis) → código
| Documento | Código |
|---|---|
| Def. 1 — sistema `M = ⟨G, Θ, Φ, Ω⟩` | `core/orchestrator.Orchestrator` (Φ orden topológico) + `core/monitor.FairnessUtilityMonitor` (Ω) |
| Def. 2 — agente `aᵢ = ⟨θᵢ, sᵢ, Lᵢ⟩` | `core/agent.MOACVAgent` (`theories`, `maturity`, `layer`) |
| Def. 3 — teoría + equivalencia por cuantización | `core/theory.Theory`, `theories_equal/similar`, `core/retrieval.similarity` (umbral δ) |
| Def. 4 — selección por ranking (U,P,K) | `core/theory.TheoryBase.select` |
| Def. 5 / 6 — `fair(W)`, `U_op(W)` | `core/fairness.fair_window`, `acc_window`, `u_op` |
| Def. 7 — cooperación (pares) | `core/sharing.cooperate`, `agent.cooperate_with` |
| Def. 8 — colaboración (maestro→aprendiz) | `core/sharing.collaborate`, `agent.transfer_to` (chequeo de nivel) |
| Def. 9 — reputación `r` / umbral `τ` | `agent.reputation`, `monitor.approve_sharing` |
| Def. 10 — amplificación `μ = b(M)/b_in` | `core/fairness.amplification` |
| Def. 11 — diversidad `D(M)` | `core/fairness.diversity` |

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

## Divergencias declaradas (honestidad)
- **Def. 7 (cooperación) — divergencia plan↔código, a resolver en el Eje 1:** el plan define
  que la cooperación "genera una base de conocimiento común θ_c" y que, para teorías
  similares, "se conserva la P **del aportante**". El código actual (`core/sharing.cooperate`)
  muta la base del **receptor** (no materializa una θ_c común) y conserva la P del receptor.
  Se resuelve contrastando con la fuente original (Maceri & García Martínez 2001;
  García-Martínez et al. 2006) antes de tocar el código — no se corrige sin la fuente.
- **μ (Def. 10):** se mide contra la **entrada**. El demo reporta dos instrumentaciones —brecha vs ground-truth y el criterio de equidad elegido— y **no valida la conjetura μ<1** (es trabajo del Eje 1; el PoC sólo demuestra el mecanismo, §5).
- **Similitud semántica:** proxy *cosine* sobre tokens `clave=valor` (sin embeddings). Upgrade a embeddings (Ollama / sentence-transformers) es directo en `core/retrieval.similarity`.
- **TBox:** antes era un dict JSON-LD plano; ahora es el esquema RDF de §2.5 con `rdflib`.
- **Ontología "curada manualmente — estado del repositorio" (§2.5):** ahora el TBox es código versionado y el ABox se genera automático.
- **"Triple store" (obs. Becerra):** lo que hay es **serialización RDF a Turtle** sobre un grafo `rdflib` en memoria, no un store persistente. El orden de ejecución NO se confía al orden de tripletas ni al `timestamp` (puede colisionar) sino a un ordinal explícito; el round-trip serializar→recuperar está testeado. Store persistente (Fuseki/GraphDB) = trabajo futuro.
- **Explicabilidad (obs. Becerra):** trazabilidad ≠ explicabilidad. La explicación se deriva del **RDF serializado** (no del estado en memoria) y se separa por destinatario (regulador / usuario). Es derivación + articulación, **no** XAI por atribución (SHAP/LIME/contrafácticos). La explicación tri-nivel L1/L2/L3 del `ExplainabilityAgent` (instancia HR) sigue siendo la del agente; la nueva derivación RDF→explicación es genérica (`core/`).
- **Compartición M2M (obs. Becerra):** hay dos caminos, complementarios. (1) En el pipeline en vivo, la cooperación/colaboración (Def. 7/8, `core/sharing.py`) opera **en memoria** entre agentes del mismo proceso. (2) `core/ontology/sharing_rdf` materializa el intercambio **estándar vía RDF** (M2M, independiente del framework): un agente exporta sus teorías a Turtle y otro las reconstruye desde el grafo. Para soportarlo, el ABox ahora serializa la tupla completa ⟨Si,A,Sf,P,K,U⟩ (antes faltaban la acción A y la situación final Sf).
