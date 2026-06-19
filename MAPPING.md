# MAPPING — código ↔ propuesta v13

La **v13 es la fuente de verdad**. Esta tabla documenta cómo los nombres y constructos
del documento (§2, §2bis, §2.5, §3, §4) se materializan en el código.

## Estructura (decoupling — P4)
- `src/moav_hr/core/` — modelo **genérico** MOACV (§2, §2bis, §3). No importa `instances/` (test: `tests/test_decoupling.py`).
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
- SPARQL (interoperabilidad / auditoría de sesgo): `core/ontology/queries.py`.
- Nombres de clases/propiedades: **idénticos a §2.5** (Agente, AgenteAuditor, Teoria, Situacion(Inicial/Final), Accion, BaseDeConocimiento, Decision, VentanaDeDecisiones, EventoDeAuditoria + subclases, Candidato, AtributoProtegido; poseeBase, contieneTeoria, registra, aplicaEn, esIgualA/esSimilarA, cooperaCon (simétrica), colaboraCon, produce, audita, ponderaComparticion, generaEvento).

## Regiones (§3) → código
Cada evento del audit trail lleva `region=N` (1–7). Región 1 = Parser; 2 = Matcher (RAG+few-shot, §2.2); 4 = Bias Auditor; 7 = decisión/evolución (Orchestrator/Monitor).

## Divergencias declaradas (honestidad)
- **μ (Def. 10):** se mide contra la **entrada**. El demo reporta dos instrumentaciones —brecha vs ground-truth y el criterio de equidad elegido— y **no valida la conjetura μ<1** (es trabajo del Eje 1; el PoC sólo demuestra el mecanismo, §5).
- **Similitud semántica:** proxy *cosine* sobre tokens `clave=valor` (sin embeddings). Upgrade a embeddings (Ollama / sentence-transformers) es directo en `core/retrieval.similarity`.
- **TBox:** antes era un dict JSON-LD plano; ahora es el esquema RDF de §2.5 con `rdflib`.
- **Ontología "curada manualmente — estado del repositorio" (§2.5):** ahora el TBox es código versionado y el ABox se genera automático.
