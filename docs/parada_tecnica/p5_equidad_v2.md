# E6 v2 · Equidad por celda (Si, A): v1 y v2 lado a lado

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

Pre-registro corto: `E6_PREREGISTRO_v2.md`. Se volvió a correr solo lo que toca α = 0,5; las corridas con α = 1 y el neutro son las de E6.

## Corrida 1: el equipo de E5 sobre los 600 casos

| Rol | Ajuste v2: aplicado · no aplicable por falta de evidencia (de las planificaciones con candidatas) | Cambios de teoría frente a α = 1 (v1 · v2) | Cambios de acción (v1 · v2) | Aciertos (α = 1 · v1 · v2) |
|---|---|---|---|---|
| Parser | 193 · 401 (de 594) | 69 · 0 | 0 · 0 | 539 · 539 · 539 |
| Semantic Matcher | 91 · 477 (de 568) | 106 · 0 | 0 · 0 | 445 · 445 · 445 |
| Explainer | 120 · 476 (de 596) | 0 · 0 | 0 · 0 | 595 · 595 · 595 |

**Matcher por grupo** (α = 1 · v1 con α = 0,5 · v2 con α = 0,5):

| Métrica | α = 1 | v1 | v2 |
|---|---|---|---|
| aciertos AR | 0,753 | 0,753 | 0,753 |
| aciertos no-AR | 0,730 | 0,730 | 0,730 |
| paridad demográfica | 0,123 | 0,123 | 0,123 |
| odds igualadas (EO) | 0,149 | 0,149 | 0,149 |
| ΔTPR | 0,149 | 0,149 | 0,149 |
| ΔFPR | 0,055 | 0,055 | 0,055 |

## Condición con sesgo programado («parámetros programados»), α = 0,5

| Magnitud | Ajuste v2 aplicado · no aplicable (de las planificaciones con candidatas) | Cambios de acción frente a α = 1 (v1 · v2) | Paridad demográfica (α = 1 · v1 · v2) | EO (α = 1 · v1 · v2) | Aciertos AR / no-AR (α = 1 · v2) | Deriva (ii) (v2) |
|---|---|---|---|---|---|---|
| detectable | 0 · 552 (de 552) | 0 · 0 | 0,160 · 0,160 · 0,160 | 0,121 · 0,121 · 0,121 | 0,823 / 0,833 · 0,823 / 0,833 | 0 |
| bajo umbral | 25 · 527 (de 552) | 0 · 0 | 0,100 · 0,100 · 0,100 | 0,038 · 0,038 · 0,038 | 0,853 / 0,850 · 0,853 / 0,850 | 0 |

**Advertencia.** Dentro de una celda con la acción fija, ê(Si, A) mide si esa acción se equivoca más con un grupo que con el otro, lo que pasa cuando la Si no captura algo relacionado con el grupo. No mide trato desigual: ese se ve en la ventana.

