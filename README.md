# Modelo de Ciclo de Vida para el Aprendizaje de Agentes Autónomos basados en Equidad

> Propuesta de tesis doctoral — Doctorado en Ingeniería con Mención en Tecnología de la Información
> Grupo de Inteligencia Artificial Aplicada (GIDSA) · DIIT-UNLaM
>
> Postulante: **Kevin Yoel Kovacs** · GIDSA — DIIT-UNLaM

---

## Resumen

Este trabajo propone un framework de orquestación multiagente con ciclo de vida adaptativo para la toma de decisiones asistida en contextos donde intervienen atributos socialmente sensibles (género, origen, edad). El framework extiende el **Modelo de Ciclo de Vida LLC (Learning Life Cycle)** con capas BIO/TBO/WIO (modelo LLC, UNLP 2010) al dominio de los agentes de lenguaje de gran escala (LLM agents).

El **caso de aplicación** es la selección de personal, elegido por la disponibilidad de datos públicos y por la existencia de vacancias verificadas en la literatura. El reclutamiento es el caso de prueba, no el tema central de la tesis.

## Aporte original

El framework aborda tres vacancias concretas del estado del arte:

1. **Teórico-formal** — No existe teoría formal de amplificación/atenuación de sesgo en cadenas de agentes coordinados. El modelo extiende BiasAmp→ (Wang & Russakovsky, ICML 2021) a grafos dirigidos acíclicos de agentes (DAG-MAS).

2. **Metodológico** — Los sistemas MAS existentes no incorporan ciclo de vida de agentes. Cada agente posee su propio ciclo de vida individual (Born→Novato→Trained→Mature) y su propia base de conocimiento de teorías ⟨Si, A, Sf, P, K, U⟩.

3. **Empírico-aplicado** — No existe un benchmark en español de sistemas multiagente para selección de personal con ground-truth demográfico. El modelo propone construirlo.

## Arquitectura

![Arquitectura del modelo](assets/arquitectura_modelo.svg)

El sistema se compone de cinco agentes especializados por rol:

| Agente | Rol |
|--------|-----|
| **Parser Agent** | Extracción y normalización del perfil. Aplica guardrails de no-retención de atributos sensibles. |
| **Semantic Matcher** | Matching semántico bidireccional candidato-puesto con RAG. |
| **Bias Auditor** | Mide el sesgo acumulado en la cadena antes de propagar la decisión. Bloquea si supera el umbral. |
| **Explainability Agent** | Genera explicaciones tri-nivel (agente / inter-agente / ecosistema). |
| **Orchestrator** | Coordina el DAG, registra el audit trail y escala a revisión humana. |

**Punto clave (corrección incorporada):** las capas BIO/TBO/WIO **no son una propiedad fija de cada agente**, sino las etapas del ciclo de vida que cada agente recorre individualmente. Todo agente nace (Born) con sus operadores BIO, se entrena (TBO) hasta el estado Trained, y aprende en producción (WIO) hasta madurar (Mature). Un agente Mature de un rol transfiere su base de teorías a un agente Novato del mismo rol mediante el mecanismo de colaboración del LLC.

## El modelo de teorías de aprendizaje

Cada agente registra su experiencia como teorías, siguiendo la formalización del LLC:

```
Teoría = ⟨Si, A, Sf, P, K, U⟩

Si = Situación inicial (contexto de evaluación del candidato)
A  = Acción (decisión del agente)
Sf = Situación final (resultado validado)
P  = Cantidad de veces que la teoría se cumple (éxitos)
K  = Cantidad de veces que se usó la teoría (usos)
U  = Función de utilidad (pondera precisión predictiva y equidad)
```

**Selección de teoría:** mayor U; ante empate, mayor P; luego menor K.

**Transferencia maestro→aprendiz:** cuando un agente Mature colabora con un Novato del mismo rol, refuerza P y K de las teorías exitosas y pondera la utilidad U, acelerando la maduración del agente novato sin reentrenar desde cero.

## Stack tecnológico

- **Orquestación:** LangGraph + LangChain
- **LLMs:** Llama 3.1 8B / Mistral 7B vía Ollama (inferencia local, sin costo de API)
- **Fairness:** Fairlearn, AIF360, métricas pipeline-level propias
- **Trazabilidad:** OpenTelemetry + Langfuse + Grafana Tempo, logging JSON-LD con ontología propia
- **Datos:** FairCVtest, JobFair, benchmark sintético propio en español (metodología FINDHR)

## Marco regulatorio

El framework está diseñado para cumplir con:
- **EU AI Act** (Reg. 2024/1689, Art. 6(2) + Anexo III §4(a)) — reclutamiento como high-risk, vigente desde agosto 2026
- **NYC Local Law 144** — bias audits anuales
- **Argentina** — Disposición 2/2023, Ley 25.326

## Estructura del proyecto

El código separa el **modelo genérico** (`core/`) de la **instancia de dominio** (`instances/hr/`) — `core/` no importa nada de `instances/` (regla verificada por test).

```
moav-hr/
├── README.md
├── MAPPING.md                       # equivalencia código ↔ propuesta v13 (§2.5, §2bis)
├── assets/arquitectura_modelo.svg
├── poc/index.html                   # PoC interactiva (abrir en navegador)
├── src/moav_hr/
│   ├── core/                        # modelo GENÉRICO (§2, §2bis, §3)
│   │   ├── agent.py · lifecycle.py · theory.py · sharing.py
│   │   ├── retrieval.py · fairness.py · monitor.py · orchestrator.py
│   │   ├── audit/                   # trail OpenTelemetry + eventos
│   │   └── ontology/               # TBox · ABox · SHACL · SPARQL (PROV-O)
│   └── instances/hr/                # INSTANCIA selección de personal (§4)
│       ├── parser_agent.py · semantic_matcher.py · bias_auditor.py
│       ├── explainability_agent.py · pipeline.py · fidelity.py
│       └── synthetic.py · scoring.py
├── experiments/run_poc.py           # demo end-to-end (sim / llm / langgraph)
├── scripts/check_env.py
└── tests/                           # core · pipeline · ontología · parser · decoupling
```

## Prueba de concepto

Hay dos PoC complementarias:

- **PoC HTML** (`poc/index.html`) — aplicación web standalone que se abre directo en el navegador, sin instalar nada. Organizada en cinco pestañas: (1) *Pipeline* de los cinco agentes sobre 12 candidatos sintéticos con audit trail en vivo; (2) *Ciclo de vida & transferencia* — madurez Born→Mature por agente y colaboración maestro→aprendiz; (3) *Teorías* ⟨Si,A,Sf,P,K,U⟩ con el criterio de selección U>P>K en vivo; (4) *Caso basal vs Modelo* — comparación de equidad; (5) *Ontología & Compliance* — evento JSON-LD y justificación.
- **PoC Python** (`src/moav_hr/` + `experiments/run_poc.py`) — implementación con el stack real (LangGraph + Ollama/Llama 3.1). Corre en modo `sim` (determinístico, liviano) o `llm` (inferencia real). Ver `src/moav_hr/README.md`.

## Cómo correr

Requiere Python 3.10+. No usa claves ni modelos propietarios; el modo `sim` corre sin LLM.

```bash
# 1. entorno
python -m venv .venv && source .venv/bin/activate
pip install -e .

# 2. (opcional, solo para modo llm) Ollama + modelo local
#    instalar Ollama (https://ollama.com) y:  ollama pull llama3.1:8b

# 3. tests
pytest tests/ -q

# 4. caso de demostración determinístico (Plan §5) — basal rechaza → modelo escala
python experiments/demo_caso.py

# 5. pipeline completo: fairness, μ/D, ontología RDF+SHACL+SPARQL, fidelidad, compartición
python experiments/run_poc.py            # modo sim
python experiments/run_poc.py --mode llm --limit 3   # con Llama real
python experiments/run_poc.py --turtle 3             # RDF/Turtle de una decisión

# 6. app web (para el video): abrir poc/index.html en el navegador (sin instalar nada)
```

Alcance hecho/futuro en [`ESTADO.md`](ESTADO.md) · mapeo código↔documento en [`MAPPING.md`](MAPPING.md).

## Estado del desarrollo

**Año 1 · 1.º sem**
- [x] Estado del arte y vacancias identificadas
- [x] Propuesta formal revisada (modelo genérico + conjetura de atenuación)
- [x] Diagrama de arquitectura
- [x] Prueba de concepto funcional (HTML interactivo + Python sobre LangGraph/Ollama)

**Año 1 · 2.º sem**
- [~] Framework con LLMs reales (LangGraph/Ollama) — pipeline operativo; calibración TBO en curso
- [ ] Caso basal sobre FairCVtest / JobFair
- [ ] Benchmark sintético en español

**Año 2 · 1.º sem**
- [ ] Experimentos de amplificación/atenuación en topologías simples
- [ ] Ontología completa (PROV-O, SHACL, orden) y explicabilidad M2M

**Año 2 · 2.º sem**
- [ ] Validación de utilidad acotada con usuarios (n ≥ 30)
- [ ] Consolidación, escritura y defensa

## Licencia

Trabajo académico en desarrollo. Todos los derechos reservados al autor mientras la tesis esté en curso.

---

*Kevin Yoel Kovacs — ORCID: 0009-0005-1127-8360*
