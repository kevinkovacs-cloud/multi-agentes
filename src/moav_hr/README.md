# Implementación Python de MOACV

PoC en Python del pipeline multiagente. Complementa la PoC HTML (`poc/index.html`)
con el stack real (LangGraph + Ollama) como evidencia de viabilidad técnica.

## Estructura

- `synthetic.py` — los 12 candidatos sintéticos + descripción del puesto (datos compartidos).
- `llm.py` — abstracción del backend LLM. Modo `sim` (determinístico, sin LLM) o `llm` (Llama 3.1 vía Ollama).
- `lifecycle/theory.py` — modelo de teorías ⟨Si, A, Sf, P, K, U⟩ y colaboración maestro→aprendiz.
- `agents/` — los 5 agentes, cada uno subclase de `MOACVAgent` con su ciclo de vida:
  - `parser_agent.py` (BIO · Mature) · `semantic_matcher.py` (TBO · Trained)
  - `bias_auditor.py` (BIO · Mature) · `explainability_agent.py` (WIO · Novato)
  - `orchestrator.py` (coordina el DAG + caso basal `run_baseline`)
- `fairness/metrics.py` — demographic parity, equalized odds, error vs ground-truth, brecha de trato.
- `fairness/dag_bias.py` — amplificación/atenuación de sesgo en la cadena (Eje 1 / Vacancia 1).
- `audit/ontology.py` — evento de decisión JSON-LD (ontología + compliance).
- `audit/trail.py` — colector de eventos del audit trail.
- `pipeline/dag.py` — el mismo DAG sobre **LangGraph** (stack de orquestación de la propuesta).

## Cómo correr

```bash
# verificar entorno (deps + Ollama + modelo)
.venv/bin/python scripts/check_env.py

# demo: pipeline MOACV (modo sim) + caso basal + fairness + amplificación de sesgo
.venv/bin/python experiments/run_poc.py

# con inferencia real de Llama (limitá la cantidad para no sobrecargar)
.venv/bin/python experiments/run_poc.py --mode llm --limit 3

# el DAG corriendo sobre LangGraph
.venv/bin/python experiments/run_poc.py --langgraph

# JSON-LD de una decisión
.venv/bin/python experiments/run_poc.py --json 3

# tests
.venv/bin/python -m pytest tests/ -q
```

> El **modo `sim`** es determinístico y reproducible (reproduce la PoC HTML). El **modo `llm`**
> demuestra el stack real end-to-end; los scores crudos del LLM están sin calibrar — la
> calibración (fine-tuning/RAG, capa TBO) es trabajo del Año 1.

## Estado

Implementado: modelo de teorías + colaboración, los 5 agentes con ciclo de vida,
fairness pipeline-level, audit trail JSON-LD, orquestación (Orchestrator + LangGraph),
demo y tests.

Pendiente (tesis): LLMs calibrados (TBO real), benchmark sintético en español,
teoremas de composición de fairness, OpenTelemetry/Langfuse en vivo.
