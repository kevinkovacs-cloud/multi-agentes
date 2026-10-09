# Métricas de equidad por rol (punto 5 del pedido)

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

Documento para la dirección. Lo generan `experiments/parada_tecnica/metricas_equidad_doc.py` y las salidas de E6 (pre-registro `E6_PREREGISTRO.md`), E6 v2 (pre-registro corto `E6_PREREGISTRO_v2.md`) y el control post hoc. Selección de personal es el dominio de experimentación.

**Planos.** El plano de decisión es lo que el rol percibe y hace (Si, A, Sf). El grupo vive solo en el plano de auditoría (Ω y los registros E): nunca entra en Si, A ni los prompts (DE-4). Toda brecha entre grupos se calcula en ese plano.

## Tres criterios que no coinciden

- **Paridad demográfica:** diferencia de la tasa de resultado favorable entre grupos. Sigue a la tasa base: si un grupo tiene más calificados, la marca aunque las decisiones sean correctas.
- **Paridad de aciertos:** diferencia de la tasa de decisiones correctas entre grupos.
- **Odds igualadas (EO):** max(|ΔTPR|, |ΔFPR|): si entre los calificados (TPR) y entre los no calificados (FPR) cada grupo recibe el mismo trato.
- **Paridad de tasa de error** (nivel celda): con la acción fija en una celda, TPR y FPR son triviales (todos los calificados de la celda reciben la misma acción); lo único no trivial es si la acción se equivoca más con un grupo. Es la base de ê(Si, A).

Ejemplo corrido (los 260 casos de E4): paridad demográfica 0,154; aciertos 0,761 (AR) y 0,746 (no-AR); TPR 0,825 y 0,667 (EO 0,158). «Los tres criterios no coinciden y responden preguntas distintas.» En los 600 casos de E6: paridad demográfica 0,123 con diferencia de calificados 0,103; aciertos 0,753 y 0,730; EO 0,149.

## Métrica de cada rol

### Parser

- **Definición:** Brecha de completitud entre grupos (resultado favorable = perfil completo); como auditoría, el d_TV del canal proxy (cota inferior, B3).
- **Fórmula:** |P(completo | AR) − P(completo | no-AR)|; d̂_TV = max(0, 2·bAcc − 1) de un clasificador grupo ~ Si del Parser, en held-out.
- **Datos y plano:** Sf del Parser (decisión); grupo (auditoría).
- **m_min:** 5 lecturas por grupo para ê.
- **Límites:** Mezcla la estrategia con lo que trae el documento (defectos de la semilla). El d_TV es una cota inferior, no el valor.
- **Valores (600 casos, α = 1):** brecha del resultado favorable 0,003 (AR 0,897, no-AR 0,900); d_TV del canal proxy 0,144.

### Semantic Matcher

- **Definición:** A nivel rol y ventana: odds igualadas. A nivel celda (en la utilidad): paridad de tasa de error, ê(Si, A). La paridad demográfica se informa para contrastar.
- **Fórmula:** EO = max(|ΔTPR|, |ΔFPR|), con la etiqueta observada (BIO y TBO: etiqueta del escenario; WIO: revisión humana). ê(Si, A) = 1 − |err(AR) − err(no-AR)| sobre E(Si, A).
- **Datos y plano:** Acción y Sf (decisión); grupo (auditoría).
- **m_min:** 5 lecturas por grupo para ê.
- **Límites:** La acción de la teoría es la decisión: dentro de una celda todos reciben la misma acción, así que la paridad demográfica por celda es trivial. La disparidad de trato surge de qué celdas y teorías se aplican a cada grupo y se mide en la ventana. En WIO la etiqueta es la revisión humana, que puede equivocarse.
- **Valores (600 casos, α = 1):** brecha del resultado favorable 0,123 (AR 0,503, no-AR 0,380); odds igualadas 0,149 (ΔTPR 0,149, ΔFPR 0,055).

### Bias Auditor

- **Definición:** Paridad de derivación Δ_esc (C5).
- **Fórmula:** |P(derivado | AR) − P(derivado | no-AR)|.
- **Datos y plano:** Acción del Auditor y grupo de cada caso de la ventana (auditoría).
- **m_min:** no aplica.
- **Límites:** La derivación es por ventana: todos los casos reciben la misma intervención y Δ_esc es 0 por construcción mientras las ventanas tengan los dos grupos por igual. U_rol no aplica: la acción la decide la regla (DE-6).
- **Valores (600 casos, α = 1):** brecha del resultado favorable 0,000 (AR 0,000, no-AR 0,000).

### Explainer

- **Definición:** Brecha de completitud de la explicación entre grupos.
- **Fórmula:** |P(completa | AR) − P(completa | no-AR)|.
- **Datos y plano:** Sf del Explainer (decisión); grupo (auditoría).
- **m_min:** 5 lecturas por grupo para ê.
- **Límites:** La completitud depende del tipo de decisión y del destinatario; si las decisiones difieren por grupo, la brecha lo arrastra.
- **Valores (600 casos, α = 1):** brecha del resultado favorable 0,017 (AR 1,000, no-AR 0,983).

## La equidad en la utilidad: U_rol con α = 0,5

U_rol = α·U + (1 − α)·ê; ê solo con al menos m_min = 5 lecturas en cada grupo.

| Rol | v1 (ê por teoría): cambios de teoría · de acción | v2 (ê por celda): ajuste aplicado · no aplicable por falta de evidencia | v2: cambios de teoría · de acción |
|---|---|---|---|
| Parser | 69 · 0 | 193 · 401 (de 594) | 0 · 0 |
| Semantic Matcher | 106 · 0 | 91 · 477 (de 568) | 0 · 0 |
| Explainer | 0 · 0 | 120 · 476 (de 596) | 0 · 0 |

- **v1** (E6): ê(t) por teoría. Cambió la teoría 175 veces y la acción 0: todas las variantes de una acción tienen la misma U y ê(t) solo las reordenaba. En 160 cambios ganó la variante sin ê: el respaldo premiaba la falta de evidencia.
- **v2** (E6 v2): ê(Si, A) sobre todas las decisiones en que se aplicó A en Si; si alguna acción candidata no tiene ê, α = 1 para todas. No cambió ninguna acción ni ninguna teoría en estas corridas. Cuando hubo evidencia para comparar, la diferencia de U entre acciones fue mayor que la de ê; en la mayoría de las planificaciones faltó evidencia sobre la acción no elegida, porque una vez aprendida la acción la otra deja de probarse. Un test (`tests/test_bloquee_e6_v2.py`) muestra que con evidencia en las dos acciones y U parecidas el ajuste sí cambia la acción.
- Los aciertos y las tasas favorables por grupo de cada rol quedaron iguales con α = 1, v1 y v2.

**Advertencia.** Dentro de una celda con la acción fija, ê(Si, A) mide si esa acción se equivoca más con un grupo que con el otro, lo que pasa cuando la Si no captura algo relacionado con el grupo. No mide trato desigual: ese se ve en la ventana.

## Condición con sesgo programado («parámetros programados»)

El sesgo entra por el rasgo proxy `titulo_local` en la Si del Matcher (regla 11): se correlaciona con el grupo y no con la verdad; el operador BIO lo penaliza.

- **Detectable** (brecha del operador 0,40; d_TV de la Si frente al grupo 0,767): paridad demográfica neutro 0,437 y Matcher que aprende 0,160; odds igualadas 0,502 y 0,121. Regla de ventana: ninguna derivación; regla acumulada: 24 ventanas del neutro (desde W07), 0 del Matcher que aprende. En E(t) de las celdas sin título local: 17 lecturas de AR y 215 de no-AR. E6 v2: ajuste aplicado en 0 de 552 planificaciones.
- **Bajo umbral** (brecha del operador 0,10; d_TV de la Si frente al grupo 0,022): paridad demográfica neutro 0,107 y Matcher que aprende 0,100; odds igualadas 0,098 y 0,038. Regla de ventana: ninguna derivación; regla acumulada: 0 ventanas del neutro, 0 del Matcher que aprende. En E(t) de las celdas sin título local: 113 lecturas de AR y 164 de no-AR. E6 v2: ajuste aplicado en 25 de 552 planificaciones.

Atenuación por aprendizaje: ilustra el mecanismo; no es evidencia de la conjetura de atenuación.

**Límite del gate de compartición** (decisión 3 de E6_RESPUESTA). El gate usa la brecha del resultado favorable, que a nivel rol es paridad demográfica: no separa la tasa base del sesgo, frena de más cuando las tasas base difieren y no ve un sesgo por debajo de lo detectable. En la condición detectable dejó pasar la colaboración del Matcher sesgado que aprende (LCB 0,000), según el estándar de evidencia acordado. Propuesta para después de la parada técnica, sin implementar: que el gate use la métrica del rol (odds igualadas para el Matcher).

**Alerta de proxy para revisión humana** (propuesta, sin implementar). El d_TV de la Si frente al grupo (B3) ya existe y dio 0,767 en la condición detectable: la Si deja inferir el grupo. Se propone mostrarlo como alerta del Monitor de Equidad, no como gate.

## Control post hoc

«Control agregado después de ver los resultados; no pre-registrado». Un Matcher que aprende sobre los mismos casos de la condición programada, sin el rasgo y con el operador BIO sin sesgo (el de P1), α = 1. Descriptivo: no cambia ninguna regla ni conclusión pre-registrada.

| Matcher (α = 1) | Estado final | Paridad demográfica | Odds igualadas | Aciertos AR / no-AR | Decisiones del operador BIO |
|---|---|---|---|---|---|
| control sin sesgo | Mature | 0,080 | 0,069 | 0,667 / 0,673 | 24,0 % |
| sesgado, detectable | Novice | 0,160 | 0,121 | 0,823 / 0,833 | 5,0 % |
| sesgado, bajo umbral | Born | 0,100 | 0,038 | 0,853 / 0,850 | 2,0 % |

Diferencia de calificados del flujo: 0,103. Con la magnitud detectable, la paridad demográfica del Matcher sesgado supera a la del control en 0,080 y las odds igualadas en 0,052. **El control no es un contrafáctico limpio:** llegó a Mature y pasó la mayor parte del flujo en WIO, donde el Matcher no explora (P3) y el operador BIO decide en las celdas nuevas; los Matchers sesgados quedaron en capas con exploración. Por eso aciertan más. La diferencia mezcla el sesgo con la dinámica del ciclo de vida.

