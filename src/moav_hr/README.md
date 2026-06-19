# Implementación Python de MOACV (alineada a la propuesta v13)

Separa el **modelo genérico** (`core/`) de la **instancia de dominio** (`instances/hr/`).
Regla no negociable (test `tests/test_decoupling.py`): **`core/` no importa `instances/`**.
La equivalencia código ↔ documento está en [`MAPPING.md`](../../MAPPING.md).

## `core/` — modelo genérico (§2, §2bis, §3)
- `agent.py` — agente `aᵢ = ⟨θᵢ, sᵢ, Lᵢ⟩` (Def. 2): ciclo de vida, RAG de teorías, reputación, compartición.
- `lifecycle.py` — estados Born→Mature, capas BIO/TBO/WIO, las 7 regiones (§3).
- `theory.py` — teoría ⟨Si,A,Sf,P,K,U⟩ con equivalencia por cuantización (Def. 3) y selección (Def. 4).
- `retrieval.py` — recuperación por similitud + few-shot (§2.2).
- `sharing.py` — cooperación (Def. 7), colaboración (Def. 8), gating por reputación (Def. 9).
- `fairness.py` — `fair(W)`, `U_op(W)` (Def. 5/6), amplificación `μ` (Def. 10), diversidad `D` (Def. 11).
- `monitor.py` — Monitor de Utilidad de Equidad Ω (§2.4): regiones 4/7 y compartición.
- `orchestrator.py` — orquestación del DAG (Def. 1, orden topológico).
- `audit/` — audit trail sobre OpenTelemetry (spans → eventos).
- `ontology/` — TBox (§2.5) + ABox automático + SHACL + SPARQL, con alineación PROV-O.

## `instances/hr/` — selección de personal (§4)
Los 5 agentes (`parser_agent`, `semantic_matcher`, `bias_auditor`, `explainability_agent`),
el `pipeline` que los cablea sobre `core.Orchestrator`, el caso basal, el harness de
`fidelity` y los datos (`synthetic`, `scoring`).

## Cómo correr

```bash
.venv/bin/python scripts/check_env.py            # verifica entorno + Ollama
.venv/bin/python experiments/run_poc.py          # demo completo (modo sim)
.venv/bin/python experiments/run_poc.py --mode llm --limit 3     # con Llama real
.venv/bin/python experiments/run_poc.py --turtle 3               # RDF/Turtle de una decisión
.venv/bin/python -m pytest tests/ -q
```

> **Honestidad (no negociable):** la conjetura de atenuación `μ<1` y la fidelidad de las
> teorías son **hipótesis a contrastar** (Ejes 1 y 3). El código provee el instrumental y
> los experimentos; **no** se fabrican ni hardcodean resultados. El modo `sim` es
> determinístico y reproducible; el modo `llm` demuestra el stack real (scores sin calibrar).
