# DERIVA NUMÉRICA de la demo — branch `eje1/formalizacion-v2` vs `main`

**Qué es esto:** la formalización v2 (A1 cuantización + A2 Laplace) mueve números del
demo. Este documento lista el antes/después con su causa, para decidir con Kevin si se
regraba algo AL MERGEAR — **no es de esta tanda: el video sale de `main`, que está
intacto**. Referencias: `/tmp/demo_base.txt` y `/tmp/poc_base.txt` (Paso 0) vs corrida
de la branch (11/07/2026).

## Lo que NO cambió (la narrativa del video sobrevive)

- **Las 12 decisiones del lote son IDÉNTICAS** (basal→modelo): Fátima y Ahmed
  ESCALATE_HUMAN, Camila REJECT, el resto ADVANCE.
- Falsos rechazos de calificados: **1 → 0** (igual).
- fair(W) = 0.833 · Ventana marcada por Ω: True · Δ ventana = 0.167 (iguales).
- Fátima: sesgo 0.100 > 0.075 ⛔ → ESCALATE → ajustado 0.850 (iguales).
- d_TV del Parser: 0.000 (nueva línea, guardrail BIO — no existía en main).

## Lo que derivó, con causa

| Métrica (demo/lote) | main | branch | Causa |
|---|---|---|---|
| Teorías sembradas (matcher) | 4 | **11** | **A1**: el esquema viejo `sim≥δ` fusionaba teorías con Si NO idénticas (umbral no transitivo — el bug corregido); con `q_canonical` la identidad es exacta |
| Teorías RAG recuperadas (típico) | 1 | **3** | consecuencia de A1: hay más teorías distintas sobre el umbral de RECUPERACIÓN (top_k=3) |
| Matcher de Fátima (id 3) | 0.820 | **0.812** | **A2**: reliability de teorías sembradas 1.0 → Laplace (p+1)/(k+2); el nudge 0.03·rel baja |
| Matcher del demo default (id 10) | 0.770 | **0.762** | ídem A2 (la decisión no cambia: bloqueado → ajustado 0.800) |
| Subestimación alto riesgo (lote) | −0.003 | **−0.006** | A2 (nudges menores) |
| Brecha de trato por grupo (lote) | 0.047 | **0.041** | A2 |
| μ_rel por brecha-vs-GT | 0.703 | **0.606** | A2 (además se RENOMBRÓ a μ_rel — N1) |
| Tripletas RDF del caso | 155 | **267** | 11 teorías serializadas en vez de 4 |
| M2M: teorías exportadas | 4 | **11** | ídem |
| Colaboración → novato (nuevas) | 4 | **11** | ídem |

## Implicación para el deck/guion (SOLO si se mergea a main)

La placa 9 y el guion citan **Matcher 0.82** (main). En la branch ese valor es 0.812 y
el μ_rel del lote pasa de 0.703 a 0.606. Decisión pendiente de Kevin al mergear:
regrabar el bloque 2 del video / regenerar deck con la corrida nueva, o mantener main
congelado hasta después de la reunión. **Ninguna decisión cambia; cambian magnitudes.**
