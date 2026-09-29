# REPORTE — Bloque C (29/09/2026)

**Rama:** `eje1/bloque-c`, creada desde `eje1/formalizacion-v2` (HEAD `0a97abc`). **Sin push, merge ni tags.** `main` no se tocó.
**Especificación:** `HANDOFF_CLAUDE_CODE_bloqueC_2026-09-29.md` (Claude chat, a partir de Génesis v2).
**Verificación en cada ítem:** `pytest -q`, `experiments/demo_caso.py 3` y `experiments/run_poc.py` (este último es determinístico: dos corridas idénticas). Después de tocar `experiments/`, además `py_compile` y corrida completa.

## 1. `pytest -q` antes y después

| | Resultado |
|---|---|
| **Antes** (baseline, rama nueva con el renombre pendiente sin commitear) | **103 passed**, 0 failed |
| **Después** (HEAD de `eje1/bloque-c`) | **129 passed, 1 xfailed**, 0 failed, 2 warnings |

- **+26 tests nuevos que pasan + 1 xfail documentado**, todos en `tests/test_bloquec_*.py`.
- El **xfail** es el criterio literal de C4 (a): ver la pregunta 1.
- Los **2 warnings** son el aviso nuevo de C7, disparado por `test_certified_monitor.py`, que llama al gate certificado con 0 y con 3 ventanas. Son esperados y ese test sigue verde.
- En C1, C2 y C9 comprobé que los tests nuevos **fallan con el código anterior** (`git stash` del archivo corregido) y pasan con el nuevo.

## 2. Ítem → commit → archivos → tests nuevos → estado

| Ítem | Commit | Archivos tocados | Tests nuevos | Estado |
|---|---|---|---|---|
| C0 | `519ff8a` | `experiments/demo_caso.py`, `src/moav_hr/README.md`, `core/__init__.py`, `core/monitor.py`, `instances/hr/pipeline.py`, `tests/test_monitor.py` | — (alias verificado en consola) | **Hecho.** El diff pendiente era 100 % texto (6 líneas). Alias `FairnessMonitor = FairnessUtilityMonitor` agregado. Aceptación: `grep "Utilidad de Equidad" src tests experiments` sin coincidencias en fuentes (solo aparece en `src/moav_hr.egg-info/PKG-INFO`, generado e ignorado por git). |
| C1 | `b3363f9` | `core/sharing.py` | `test_bloquec_merge.py` (3) | **Hecho.** `u = Σk_own·u / Σk_own`. Promedio simple si Σk_own = 0. Una variante de una sola teoría conserva su `u` literal, porque `(k·u)/k ≠ u` en punto flotante. Docstring: regla provisoria hasta la decisión 2. `test_sharing_fuente.py` sigue verde. |
| C2 | `f8c39df` | `core/theory.py` | `test_bloquec_reliability.py` (2) | **Hecho.** `reliability = (p+1)/(k_own+2)`. `test_laplace.py` sigue verde. Ningún test existente asumía el denominador `k` después de una fusión. |
| C3 | `7afbf8f` | `core/theory.py`, `core/ontology/abox.py`, `core/ontology/sharing_rdf.py` | `test_bloquec_iris.py` (3) | **Hecho.** `theory_key` + `theory_iri`. El grep de IRIs posicionales queda vacío. `sharing_rdf` reconstruye desde los literales (no parsea IRIs). `theories_to_turtle` gana un parámetro `q` opcional (default `q_canonical`). `test_m2m_teorias.py` sigue verde. Ver preguntas 2 y 3. |
| C4 | `e6ae99c` | `core/ontology/tbox.py`, `abox.py`, `sharing_rdf.py` | `test_bloquec_rdf_u.py` (4 + 1 xfail) | **Parcial.** Hecho: `U` sin `round`; `usos` = `k_own` declarado en la TBox, exportado en ABox y M2M e importado (`k_own` se reconstruye desde `usos`); SHACL conforme. **Falta:** la ida y vuelta **exacta por Turtle**, que no se puede con `xsd:double` en rdflib 7.6 (pregunta 1). |
| C5 | `e3e33c9` | `core/fairness.py`, `experiments/run_poc.py` | `test_bloquec_esc.py` (3) | **Hecho.** `escalation_disparity` (caso Simpson: Δ_esc = 0.8 con Δ_DP = 0). `run_poc`: una línea nueva `Δ_esc` en B2; `log_run` con `delta_esc`, `mu_rel_auto`, `mu_rel_total` y `d_modelo_pos_incluye_escalados`. No cambió ninguna línea impresa existente: los `amplification` se recalculan en variables sin tocar los `print`. |
| C6 | `07edc66` | `instances/hr/pipeline.py`, `experiments/run_poc.py`, `MAPPING.md` | `test_bloquec_window.py` (3) | **Hecho.** `escalate_window` y el flag `--window-escalation {off,point,certified}` (default `off`). **Con `off` la salida es idéntica** a la del commit anterior (diff vacío). `point` bloquea y manda 12/12 a revisión humana. `certified` no bloquea con n = 12 (pregunta 6). |
| C7 | `b48f670` | `core/stats.py`, `core/monitor.py` | `test_bloquec_gate.py` (3) | **Hecho.** `m_min_gate` (47 / 82 verificados). Warning si `n < m_min_gate(1.0, τ, δ)`, protegido para τ ≥ 1. El retorno no cambia y `run_poc` sigue con el gate puntual. `test_certified_monitor.py` sigue verde. |
| C8 | `fb21f32` | `core/agent.py`, `tests/test_monitor.py` | — | **Hecho.** Solo comentario y docstring, sin cambios de comportamiento. |
| C9 | `3b5b4c5` | `core/retrieval.py`, `ESTADO.md` | `test_bloquec_retrieve.py` (2) | **Hecho.** Clave `(-u, -p, k, -created_at, id)`. Línea agregada en `ESTADO.md`. Demo y `run_poc` idénticos: el lote no tiene empates exactos. |
| C10 | `653ba95` | `core/stats.py` | `test_bloquec_power.py` (3) | **Hecho.** Docstring de `min_window` corregido (el valor de retorno no cambia) y `n_power` nuevo (9530 / 2383). Verificación empírica con 4000 ventanas: potencia **0.370** en el n de `min_window` (738) y **0.997** con `n_power` (2383). |
| C11 | `7e270a9` | `ESTADO.md`, `MAPPING.md` | — | **Hecho.** Sección «Bloque C (29/09/2026)» en ambos archivos, con el Bloque B **listado sin implementar**. |

**Efecto de cada ítem en las salidas de los scripts** (comparando contra el anterior; se normaliza el ID de traza aleatorio del demo):

| Ítem | `demo_caso.py` | `run_poc.py` |
|---|---|---|
| C1, C2, C7, C8, C9, C10 | sin cambios | sin cambios |
| C3 | cambia el paso [7] (IRIs largos, otra teoría de ejemplo) | sin cambios |
| C4 | 267 → 278 tripletas; el Turtle crece | 1059 → 1070 tripletas (+11 triples `usos`) |
| C5 | sin cambios | +1 línea `Δ_esc` |
| C6 | sin cambios | idéntico con `off` |

## 3. `git diff --stat eje1/formalizacion-v2..eje1/bloque-c` (sin contar este reporte)

```
 ESTADO.md                                | 30 +++++++++++
 MAPPING.md                               | 18 +++++++
 experiments/demo_caso.py                 |  2 +-
 experiments/run_poc.py                   | 39 +++++++++++++-
 src/moav_hr/README.md                    |  2 +-
 src/moav_hr/core/__init__.py             |  2 +-
 src/moav_hr/core/agent.py                |  4 ++
 src/moav_hr/core/fairness.py             | 17 ++++++
 src/moav_hr/core/monitor.py              | 19 ++++++-
 src/moav_hr/core/ontology/abox.py        | 40 +++++++++++---
 src/moav_hr/core/ontology/sharing_rdf.py | 31 +++++++----
 src/moav_hr/core/ontology/tbox.py        |  3 ++
 src/moav_hr/core/retrieval.py            |  6 ++-
 src/moav_hr/core/sharing.py              | 24 +++++++--
 src/moav_hr/core/stats.py                | 45 ++++++++++++++--
 src/moav_hr/core/theory.py               | 29 +++++++++-
 src/moav_hr/instances/hr/pipeline.py     | 12 ++++-
 tests/test_bloquec_esc.py                | 40 ++++++++++++++
 tests/test_bloquec_gate.py               | 45 ++++++++++++++++
 tests/test_bloquec_iris.py               | 75 ++++++++++++++++++++++++++
 tests/test_bloquec_merge.py              | 86 ++++++++++++++++++++++++++++++
 tests/test_bloquec_power.py              | 36 +++++++++++++
 tests/test_bloquec_rdf_u.py              | 90 ++++++++++++++++++++++++++++++++
 tests/test_bloquec_reliability.py        | 38 ++++++++++++++
 tests/test_bloquec_retrieve.py           | 34 ++++++++++++
 tests/test_bloquec_window.py             | 50 ++++++++++++++++++
 tests/test_monitor.py                    |  4 +-
 27 files changed, 785 insertions(+), 36 deletions(-)
```

## 4. PREGUNTAS PARA CLAUDE CHAT

1. **C4: la especificación choca con rdflib.** El serializador **Turtle** de rdflib 7.6.0 escribe `xsd:double` en forma abreviada con `"%e"`: `2/3` sale como `6.666667e-01`, con 7 cifras. Sin el `round`, la ida y vuelta es exacta en el grafo en memoria y en **N-Triples, JSON-LD y RDF/XML**, y en Turtle solo si se usa **`xsd:decimal`**. Todo verificado. El criterio (a) («Turtle → exactamente 2/3») no se puede cumplir con `xsd:double` en Turtle. ¿Qué se elige?
   - (a) `U` como `xsd:decimal`: exacto en Turtle, pero cambia el datatype de `U` en la TBox.
   - (b) Mantener `xsd:double` y hacer el intercambio M2M en N-Triples o JSON-LD.
   - (c) Aceptar las 7 cifras y documentarlo.

   El criterio literal quedó como `xfail(strict=True)`: si se resuelve, el test avisa con un XPASS.
2. **C3: IRIs largos.** Como la clave es el JSON canónico de la situación, escapado, los IRIs crecen mucho.
   - En `demo_caso.py` [7] el Turtle pasa de 9.284 a 23.683 caracteres, y la teoría de ejemplo que se imprime es otra, porque rdflib ordena por IRI.
   - El demo de `main` (el del video) no cambia, pero si esta rama se mergea, cambia el paso [7] del video 2.
   - ¿Se acepta así, o se usa un **hash** de la clave, que es corto, estable y prácticamente inyectivo pero se aparta del esquema `quote()` de la especificación?
   - Supuesto nuevo que queda implícito: dos teorías de una base con la misma clave colapsarían en un solo nodo RDF. Hoy no pasa, porque `learn` deduplica con `find_equal` y `_merge` produce una teoría por variante.
3. **C3: "repr estable".** Si `Q` devuelve `str` (`q_canonical`: JSON canónico), la clave lo usa tal cual; `serialize` solo se aplica a lo que no es `str` (por ejemplo, la tupla de `q_grid`). `serialize(q(si))` literal habría codificado dos veces el JSON y alargado más el IRI. ¿OK?
4. **C0: el nombre viejo sigue fuera del alcance del grep.**
   - Archivos rastreados: `README.md` de la raíz (l. 33, que además se copia al `egg-info` generado) y `ESTADO.md` (l. 17).
   - Documentos locales ignorados por git: `DEMO_GUION.md`, `GUIA_UI_LOCAL.md` y `ONBOARDING_CLAUDE.md`.
   - No los toqué porque no estaban en C0. ¿Los corrijo?
5. **C1: caso borde.** El promedio simple cuando no hay evidencia (Σ k_own = 0) **no es asociativo**; lo documenté en el docstring. ¿Se deja así hasta la decisión 2?
6. **C6: modo `certified` e interacción con otras métricas.**
   - Con n = 12 (6 por grupo) el modo `certified` **no bloquea**, lo cual es coherente con C10: `n_power(0.10)` = 2383 por grupo. Si «escalamiento por ventana como default» (Bloque B) se adopta con el modo certificado, hacen falta ventanas mucho más grandes.
   - Con `point` activo, las métricas posteriores a B2 (`amp_dp`, `d_modelo_pos_incluye_escalados`) ven la ventana entera escalada.
7. **C6: trazabilidad del registro.** `vars(args)` ahora incluye `window_escalation`, así que el `config_sha` de una misma corrida por defecto cambia antes y después de C6. Las entradas de `runs/registry.jsonl` de antes y de después no se pueden comparar por `config_sha`.
8. **C5: μ_rel en la corrida por defecto.** `mu_rel_auto` y `mu_rel_total` se registran como `None`, porque la disparidad basal es 0 (caso degenerado de la Def. 10). Va con la decisión de **b_in** (Bloque B). Es solo informativo: se implementó como pide la especificación, con el `.mu` de los `amplification`.
9. **C2: efecto en el matcher.** `reliability` alimenta el score del matcher (`semantic_matcher.py`: `THEORY_NUDGE * top.reliability`). Después de una fusión, ese score puede cambiar. En la corrida por defecto no cambió.

## 5. Tests existentes modificados

- **`tests/test_monitor.py`**:
  - En **C0**: renombre de su docstring ("Monitor de Utilidad de Equidad" → "Monitor de Equidad"), que era parte del diff pendiente.
  - En **C8**: corrección del comentario pedida por la especificación.
  - En los dos casos es solo texto: **no cambió ninguna aserción ni la lógica**.
- **Ningún otro test existente se modificó.** `test_sharing_fuente.py`, `test_laplace.py`, `test_m2m_teorias.py` y `test_certified_monitor.py` siguen verdes sin cambios.
