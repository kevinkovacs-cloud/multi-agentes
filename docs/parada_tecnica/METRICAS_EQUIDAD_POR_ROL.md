# Métricas de equidad por rol (punto 5 del pedido)

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

Documento para la dirección, generado por `experiments/parada_tecnica/p5_metricas_equidad.py`. Reglas pre-registradas en `E6_PREREGISTRO.md`. Corrida 1: el equipo de E5 sobre 600 casos, con α = 1 y α = 0,5. Corrida 2: condición con sesgo programado («parámetros programados»).

**Planos.** Los datos del plano de decisión son lo que el rol percibe y hace (Si, A, Sf). El grupo vive solo en el plano de auditoría (Ω y E(t)): nunca entra en Si, A ni los prompts (DE-4). Toda brecha entre grupos se calcula en ese plano.

**U_rol (DE-5).** U_rol(t) = α·U(t) + (1 − α)·ê(t), con ê(t) = 1 − |err(AR) − err(no-AR)| sobre E(t) (las decisiones en que t fue el plan). Solo con al menos m_min = 5 lecturas en cada grupo; si no, se usa α = 1 y se registra.

## Parser

- **Definición:** Brecha de completitud de la extracción entre grupos; métrica de auditoría adicional: d_TV del canal proxy (cota inferior, B3).
- **Fórmula:** |P(completo | AR) − P(completo | no-AR)|; d̂_TV = max(0, 2·bAcc − 1) de un clasificador grupo ~ Si del Parser en held-out.
- **Datos y plano:** Sf del Parser (decisión); grupo (auditoría).
- **m_min:** 5 lecturas por grupo para ê(t).
- **Límites:** La brecha mezcla la estrategia elegida con lo que trae el documento (defectos de esta semilla, E5). El d_TV es una cota inferior, no el valor.
- **Valores (α = 1 · α = 0,5):** brecha del resultado favorable 0,003 · 0,003 (tasas AR 0,897, no-AR 0,900 con α = 1); teorías con ê(t) (m_min en los dos grupos): 6 de 6 · 10 de 11.
- **d_TV del canal proxy (cota inferior):** 0,144 (α = 1).
- **¿α = 0,5 cambió la elección?** Se usó ê(t) en 519 de 600 planificaciones; la teoría elegida cambió respecto de α = 1 en 69 (la acción, en 0; en 63 la elegida no tenía ê(t) y la de α = 1 sí).

## Semantic Matcher

- **Definición:** Paridad de errores (equalized odds) en la ventana y en la corrida; por teoría, ê(t) desde E(t). La paridad demográfica se informa para contrastar.
- **Fórmula:** EO = max(|ΔTPR|, |ΔFPR|) con la etiqueta observada (BIO y TBO: etiqueta del escenario; WIO: revisión humana); ê(t) = 1 − |err(AR) − err(no-AR)|.
- **Datos y plano:** Acción y Sf (decisión); grupo (auditoría).
- **m_min:** 5 lecturas por grupo para ê(t).
- **Límites:** Advertencia formal: la acción de la teoría es la decisión; dentro de una celda todos reciben la misma acción, así que la paridad demográfica por teoría es trivial y ê(t) usa paridad de errores, que necesita Sf. La disparidad de trato surge de qué teorías se aplican a cada grupo y se mide en la ventana. En WIO la etiqueta es la revisión humana, que puede equivocarse (ε).
- **Valores (α = 1 · α = 0,5):** brecha del resultado favorable 0,123 · 0,123 (tasas AR 0,503, no-AR 0,380 con α = 1); teorías con ê(t) (m_min en los dos grupos): 22 de 38 · 25 de 50.
- **Paridad de errores (EO):** 0,149 · 0,149 (ΔTPR 0,149, ΔFPR 0,055 con α = 1). **Paridad demográfica:** 0,123; diferencia de calificados del flujo: 0,103. En los primeros 260 casos (los de E4): paridad demográfica 0,154, aciertos 0,761 (AR) y 0,746 (no-AR), pero EO 0,158: TPR 0,825 (AR, 57 casos con Sf calificado) frente a 0,667 (no-AR, 45). La paridad de aciertos pareja no implica odds igualadas.
- **¿α = 0,5 cambió la elección?** Se usó ê(t) en 189 de 600 planificaciones; la teoría elegida cambió respecto de α = 1 en 106 (la acción, en 0; en 97 la elegida no tenía ê(t) y la de α = 1 sí).

## Bias Auditor

- **Definición:** Paridad de derivación Δ_esc (C5).
- **Fórmula:** |P(derivado | AR) − P(derivado | no-AR)|.
- **Datos y plano:** Acción del Auditor y grupo de cada caso de la ventana (auditoría).
- **m_min:** no aplica: la acción la decide la regla certificada (DE-6), así que ninguna teoría es plan y E(t) queda vacío; U_rol no interviene.
- **Límites:** La derivación es por ventana: todos los casos de una ventana reciben la misma intervención, así que Δ_esc es 0 por construcción mientras las ventanas tengan los dos grupos por igual. Con ventanas de 20 la regla certificada no puede derivar.
- **Valores (α = 1 · α = 0,5):** brecha del resultado favorable 0,000 · 0,000 (tasas AR 0,000, no-AR 0,000 con α = 1); teorías con ê(t) (m_min en los dos grupos): 0 de 0 · 0 de 0.

## Explainer

- **Definición:** Brecha de completitud de la explicación entre grupos.
- **Fórmula:** |P(completa | AR) − P(completa | no-AR)|.
- **Datos y plano:** Sf del Explainer (decisión); grupo (auditoría).
- **m_min:** 5 lecturas por grupo para ê(t).
- **Límites:** La completitud depende del tipo de decisión y del destinatario; si las decisiones difieren por grupo, la brecha lo arrastra.
- **Valores (α = 1 · α = 0,5):** brecha del resultado favorable 0,017 · 0,017 (tasas AR 1,000, no-AR 0,983 con α = 1); teorías con ê(t) (m_min en los dos grupos): 4 de 4 · 4 de 4.
- **¿α = 0,5 cambió la elección?** Se usó ê(t) en 542 de 600 planificaciones; la teoría elegida cambió respecto de α = 1 en 0 (la acción, en 0; en 0 la elegida no tenía ê(t) y la de α = 1 sí).

## Casos en que α = 0,5 cambia la teoría elegida

- Parser, ciclo 50 (WIO): con α = 0,5 eligió T12 (diccionario_sinonimos); con α = 1 habría elegido T7 (diccionario_sinonimos). Candidatas: T12 diccionario_sinonimos (U 0,857, ê —, U_rol 0,857); T7 diccionario_sinonimos (U 0,857, ê 0,833, U_rol 0,845); T4 reglas_estrictas (U 0,333, ê —, U_rol 0,333).
- Semantic Matcher, ciclo 130 (WIO): con α = 0,5 eligió T20 (ADVANCE); con α = 1 habría elegido T9 (ADVANCE). Candidatas: T20 ADVANCE (U 0,769, ê —, U_rol 0,769); T9 ADVANCE (U 0,769, ê 0,600, U_rol 0,685).

**Lo que se observa.** α = 0,5 cambió la teoría elegida 175 veces y la acción 0: con U basada en la acción (v2), todas las variantes (Si, A, ·) tienen la misma U, y ê(t) solo reordena variantes de la misma acción. En 160 de esos cambios la variante elegida no tenía ê(t) y la de α = 1 sí: el respaldo «sin ê se usa α = 1» favorece a la variante sin evidencia frente a la que tiene ê < 1.

## Condición con sesgo programado: qué mide cada métrica

«Parámetros programados». El sesgo entra por el rasgo proxy `titulo_local` en la Si del Matcher (regla 11); el grupo sigue fuera del plano de decisión. La paridad demográfica por ventana lo detecta; ê(t) casi no puede verlo: las teorías de las celdas sin título local tienen pocas lecturas del grupo AR.
- **Detectable** (brecha del operador 0,40): paridad demográfica en toda la corrida, neutro 0,437, Matcher que aprende 0,160 (α = 1) y 0,160 (α = 0,5); EO 0,502 y 0,121. La regla acumulada deriva 24 ventanas del neutro (desde W07) y 0 del Matcher que aprende.
- **Bajo umbral** (brecha del operador 0,10): paridad demográfica en toda la corrida, neutro 0,107, Matcher que aprende 0,100 (α = 1) y 0,100 (α = 0,5); EO 0,098 y 0,038. La regla acumulada deriva 0 ventanas del neutro y 0 del Matcher que aprende.

Diferencia de calificados entre grupos en el flujo (tasa base, sin sesgo): 0,103.
- **Detectable:** d_TV de la Si del Matcher frente al grupo (cota inferior) 0,767; en las teorías sin título local del Matcher con α = 1 hay 17 lecturas de AR y 215 de no-AR en E(t), y 0 de 25 llegan a m_min en los dos grupos.
- **Bajo umbral:** d_TV de la Si del Matcher frente al grupo (cota inferior) 0,022; en las teorías sin título local del Matcher con α = 1 hay 113 lecturas de AR y 164 de no-AR en E(t), y 12 de 27 llegan a m_min en los dos grupos.

