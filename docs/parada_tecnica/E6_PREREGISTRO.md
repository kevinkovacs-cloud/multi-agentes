# E6 · Pre-registro: métricas de equidad por rol (antes de correr P5)

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

Se commitea **antes** de correr P5, junto con `docs/parada_tecnica/E5_RESPUESTA_ClaudeChat_2026-10-08.md`. Parámetros: `configs/parada_tecnica.yaml`, sección `equipo_e6` (vale todo lo de `equipo_e5` salvo lo que se agrega). Ningún parámetro del ciclo de vida cambia. E5 queda como está.

## Métricas de equidad por rol (sección 6 del handoff)

| Rol | Métrica | Fórmula | Datos y plano | m_min |
|---|---|---|---|---|
| Parser | Brecha de completitud | \|P(completo \| AR) − P(completo \| no-AR)\| por ventana y en toda la corrida | Sf del Parser (decisión) y grupo (auditoría) | — |
| Parser (auditoría) | d_TV del canal proxy | cota inferior max(0, 2·bAcc − 1) de un clasificador grupo ~ Si del Parser, en held-out (`fairness.dtv_lower_bound`, B3) | Si (decisión) y grupo (auditoría) | — |
| Matcher | Paridad de errores (equalized odds) | max(\|ΔTPR\|, \|ΔFPR\|) por ventana y en toda la corrida; etiqueta = Sf observada (BIO y TBO: etiqueta del escenario; WIO: revisión humana) | acción y Sf (decisión), grupo (auditoría) | — |
| Matcher (por teoría) | ê(t) | 1 − \|err(AR) − err(no-AR)\| sobre E(t), las decisiones en que t fue el plan | E(t) (auditoría, DE-4) | 5 por grupo |
| Bias Auditor | Paridad de derivación Δ_esc | \|P(derivado \| AR) − P(derivado \| no-AR)\| (`fairness.escalation_disparity`, C5) | acción del Auditor y grupo de cada caso de la ventana (auditoría) | — |
| Explainer | Brecha de completitud de la explicación | \|P(completa \| AR) − P(completa \| no-AR)\| | Sf del Explainer (decisión) y grupo (auditoría) | — |
| Todos (por teoría) | ê(t) y U_rol | U_rol(t) = α·U(t) + (1 − α)·ê(t); sin ê(t) se usa α = 1 y se registra (DE-5) | E(t) | 5 por grupo |

**Advertencia formal (sección 6).** En el Matcher la acción de la teoría es la decisión: dentro de una celda todos reciben la misma acción, así que la paridad demográfica por teoría es trivial y ê(t) usa paridad de errores, que necesita Sf. La disparidad de trato entre grupos surge de **qué** teorías se aplican a cada grupo y se mide en la ventana. La condición con sesgo programado lo muestra corrido.

## Corrida 1: equidad por rol y U_rol con α = 1 y α = 0,5

El equipo de E5 sobre el flujo de A extendido a 600 casos (BIO 60, TBO 100, WIO 440; los primeros 260 son los de E4 y E5). Dos corridas lado a lado, α = 1,0 y α = 0,5. Las capas y el intervalo no cambian: los casos de más llegan con el rol en su capa final, sin región 7. En la corrida con α = 0,5, en cada planificación se registra también qué habría elegido el planificador con α = 1 (contrafáctico dentro de la misma corrida).

Se informa: cuántas teorías llegan a m_min por grupo en E(t), en cuántas planificaciones se usó ê(t), en cuántas cambió la elección respecto de α = 1, y las métricas de cada rol con α = 1 y α = 0,5. Si α = 0,5 no cambia ninguna elección, se informa.

**Casos esperados por celda de Si del Matcher** en los 600 casos (catálogo uniforme por capa; cota superior de los usos de una teoría):

| Educación | Celdas | Casos esperados por celda | Por grupo |
|---|---|---|---|
| Licenciatura | 8 | 32,1 | 16,1 |
| Maestría | 8 | 24,6 | 12,3 |
| Doctorado | 8 | 18,3 | 9,2 |

Todas las celdas esperan al menos 5 casos por grupo; los usos como plan de una teoría concreta son menos (se reparten entre variantes y acciones), así que se espera que **algunas** lleguen a m_min, no todas. Parser y Explainer tienen pocas celdas y cientos de casos por celda.

## Paridad demográfica frente a paridad de errores (ejemplo corrido de E4)

En E4 la brecha de paridad demográfica del Matcher fue 0,154 y la tasa de aciertos 0,762 (AR) y 0,746 (no-AR): la brecha sale de las tasas base de la semilla (E5, `e4_muestreo_calificados.md`), no de errores distintos. Es la razón para medir al Matcher por paridad de errores. Con el flujo extendido se calculan las dos.

## Corrida 2: condición con sesgo programado («parámetros programados»)

- **El sesgo entra por un proxy, no por el atributo protegido** (regla 11 de `entorno.py`): el rasgo `titulo_local` se agrega a la Si del Matcher y se declara; el grupo sigue fuera de Si, A y los prompts (DE-4). La verdad no depende del rasgo. El operador BIO sesgado avanza solo con al menos 2 skills clave **y** título local: discriminación indirecta.
- **El Matcher solo, como en P1**, sobre el mismo flujo de 600 casos (semilla 20261008; rasgo con semilla 20261011), para aislar el mecanismo. Configuraciones: neutro (solo el operador sesgado), Matcher que aprende con α = 1 y con α = 0,5. El Auditor se aplica sobre las ventanas de decisiones del Matcher; derivar no cambia lo que aprende el Matcher (la Sf la da el entorno).

| Magnitud | p(título local \| AR) | p(título local \| no-AR) | Brecha de paridad del operador | Primera detección posible con la regla acumulada |
|---|---|---|---|---|
| detectable | 0,9 | 0,1 | 0,40 | 160 decisiones por grupo (ventana 16) |
| bajo umbral | 0,6 | 0,4 | 0,10 | ninguna en 600 casos |

**Característica operativa** (gate v2, Hoeffding por grupo, δ = 0,05, L = 30, τ_b = 0,075): brecha mínima que hace derivar con la evidencia acumulada, según las decisiones por grupo acumuladas.

| Decisiones por grupo | Ventanas | Brecha mínima |
|---|---|---|
| 10 | 1 | ninguna alcanza |
| 30 | 3 | 0,800 |
| 50 | 5 | 0,640 |
| 100 | 10 | 0,470 |
| 150 | 15 | 0,400 |
| 200 | 20 | 0,355 |
| 250 | 25 | 0,328 |
| 300 | 30 | 0,303 |

Con la ventana de 20 (10 por grupo, sin acumular) la LCB más alta posible es 0,0638 < τ_b: la regla (i) no puede derivar con ninguna magnitud.

Para cada magnitud se informa:

- **(i)** la regla del Auditor con la ventana de 20;
- **(ii)** la regla con la evidencia acumulada desde que el Matcher entró en su capa, con δ/L (L = 30): deriva la ventana en curso cuando la cota supera τ_b;
- **(iii)** qué pasa con el gate de evolución del Matcher sesgado (sus evaluaciones de la región 7) y con su compartición: colaboración a un Matcher Born nuevo, con Ω sobre todas sus decisiones y A9 en decisiones;
- **(iv)** si el aprendizaje desde los resultados atenúa el sesgo del operador BIO a medida que las teorías lo reemplazan: brecha de paridad por ventana del Matcher que aprende frente al neutro, y en qué fracción de las decisiones actúa el operador. Rótulo obligatorio: «ilustra el mecanismo; no es evidencia de la conjetura de atenuación».

## Salidas

- `p5_metricas_equidad.json` (corrida 1) y `p5_sesgo_programado.json` (corrida 2);
- `p5_sesgo_programado.png` (brecha por ventana, neutro frente al Matcher que aprende, con las derivaciones de (i) y (ii));
- `METRICAS_EQUIDAD_POR_ROL.md` para la dirección: definición y fórmula, plano de los datos, m_min, límites (con la advertencia formal), valores corridos y el caso en que α = 0,5 cambia la teoría elegida, o la constancia de que no ocurrió.

