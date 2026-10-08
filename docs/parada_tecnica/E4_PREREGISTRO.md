# E4 · Pre-registro: todos los roles con su ciclo de vida (antes de correr P4)

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

Reglas fijadas **antes** de correr P4. Fuente: `src/moav_hr/instances/hr/entorno.py` (reglas 7 a 10) y `src/moav_hr/instances/hr/estrategias_llc.py`; parámetros: `configs/parada_tecnica.yaml`, sección `equipo_e4`. Los parámetros del ciclo de vida son los de la v2, iguales para todos los roles. Un test (`tests/test_bloquee_entorno_e4.py`) verifica que el código de las estrategias cumple las tablas de este documento.

## El equipo

- **DAG por ventana de 20 casos,** orquestado con LangGraph (`core/grafo.py`): Parser → Semantic Matcher → Bias Auditor → Orchestrator → Explainer. El Orchestrator no tiene teorías (DE-7): registra la decisión final y el escalamiento.
- **Flujo de casos:** los escenarios BIO, TBO, WIO de P1 v2 (semilla 20261008), 260 casos y 13 ventanas.
- **Cada rol transita su propia capa** (la de su estado ganado) con su propio ciclo de vida: contadores, intervalos y región 7. El escenario solo fija qué casos llegan. Es una adaptación declarada: en el LLC cada SAR tiene un escenario por capa; en el DAG los roles comparten el caso.
- **Capa agotada sin promoción, o Mature:** el rol sigue actuando y aprendiendo (regiones 1 a 6) sin evaluar la región 7.
- **Gate de Ω de cada rol** (generalización declarada del gate v2): Ω niega la promoción si LCB_δ/L(|brecha|) > τ_b, donde la brecha es la del resultado favorable del rol entre grupos: decisión ADVANCE (Matcher), perfil completo (Parser), explicación completa (Explainer), ventana derivada (Bias Auditor). El atributo protegido sigue fuera de Si, A y los prompts (DE-4).
- **α = 1,0** en P4 (LLC puro); α = 0,5 se compara en E6.

## Parser (regla 7)

Operador BIO: **reglas estrictas**. Con probabilidad 0,1 el documento omite la educación (completo pasa a parcial). u = 1 completo, 0,5 parcial, 0 fallido o con fuga.

| Plantilla (formato · estructura · etiquetas) | Frec. AR | Frec. no-AR | Reglas estrictas | Diccionario de sinónimos | u esperada (estrictas / diccionario) |
|---|---|---|---|---|---|
| json · plano · canonicas | 0,20 | 0,15 | completo | completo | 0,950 / 0,950 |
| json · plano · sinonimos | 0,15 | 0,20 | fallido | completo | 0,000 / 0,950 |
| json · anidado · canonicas | 0,20 | 0,10 | completo | fallido | 0,950 / 0,000 |
| texto · etiquetado · canonicas | 0,20 | 0,15 | completo | parcial | 0,950 / 0,500 |
| texto · libre · ninguna | 0,10 | 0,15 | fallido | completo | 0,000 / 0,950 |
| html · etiquetado · sinonimos | 0,15 | 0,25 | fallido | completo | 0,000 / 0,950 |

| Grupo | P(completo) con el operador BIO | P(completo) con la mejor estrategia por plantilla |
|---|---|---|
| AR | 0,540 | 0,900 |
| no-AR | 0,360 | 0,900 |

- **Canal proxy declarado (B3):** la plantilla depende del grupo; d_TV entre las dos distribuciones de plantilla = 0,200. La Si del Parser no contiene el atributo protegido, pero lo deja inferir en parte.
- **Brecha esperada de completitud** con el operador BIO: 0,180; con la mejor estrategia por plantilla: 0. Es lo que el aprendizaje del Parser puede cerrar.
- **Efecto en cadena (regla 8):** el Matcher percibe el perfil extraído. Un perfil parcial o fallido produce una Si distinta de la del candidato (educación «—», banda junior, 0 skills), fuera del catálogo de P1.

## Explainer (regla 10)

Operador BIO: **por factores**. u = 1 si la explicación está completa (verificada contra el grafo RDF del caso por SPARQL), 0 si no. Determinista por celda.

| Si (tipo · destinatario · motivos) | Requisitos | Por factores | Contrafáctica | Regulatoria |
|---|---|---|---|---|
| avanza · regulador · uno | dictamen_omega, motivo_principal, resultado, secuencia_trazable | incompleta | incompleta | completa |
| avanza · regulador · varios | dictamen_omega, factores_todos, motivo_principal, resultado, secuencia_trazable | incompleta | incompleta | completa |
| avanza · usuario · uno | lenguaje_llano, motivo_principal, resultado | completa | completa | incompleta |
| avanza · usuario · varios | lenguaje_llano, motivo_principal, resultado | completa | completa | incompleta |
| rechaza · regulador · uno | dictamen_omega, motivo_principal, resultado, secuencia_trazable | incompleta | incompleta | completa |
| rechaza · regulador · varios | dictamen_omega, factores_todos, motivo_principal, resultado, secuencia_trazable | incompleta | incompleta | completa |
| rechaza · usuario · uno | accion_sugerida, lenguaje_llano, motivo_principal, resultado | incompleta | completa | incompleta |
| rechaza · usuario · varios | accion_sugerida, lenguaje_llano, motivo_principal, resultado | incompleta | completa | incompleta |
| deriva · regulador · uno | dictamen_omega, motivo_principal, resultado, revision_humana, secuencia_trazable | incompleta | incompleta | completa |
| deriva · regulador · varios | dictamen_omega, factores_todos, motivo_principal, resultado, revision_humana, secuencia_trazable | incompleta | incompleta | completa |
| deriva · usuario · uno | lenguaje_llano, motivo_principal, resultado, revision_humana | incompleta | completa | incompleta |
| deriva · usuario · varios | lenguaje_llano, motivo_principal, resultado, revision_humana | incompleta | completa | incompleta |

- **Elementos de cada estrategia:** por factores: factores_todos, lenguaje_llano, motivo_principal, resultado; contrafáctica: accion_sugerida, lenguaje_llano, motivo_principal, resultado, revision_humana; regulatoria: dictamen_omega, factores_todos, motivo_principal, resultado, revision_humana, secuencia_trazable.
- **Motivos** no cambia la mejor estrategia en ninguna celda: está en la Si porque lo pide la sección 6 del handoff; se informa.

## Bias Auditor (regla 9, DE-6)

Un ciclo por ventana de 20 casos (10 por grupo). La acción la decide la regla certificada (DERIVAR si LCB_δ(|Δ_DP|) > τ_b), no la teoría. La revisión confirma sesgo con el mismo estándar sobre la brecha de tasas de error del Matcher.

- **LCB más alta posible** con 10 por grupo (brecha observada 1): 0,0638, frente a τ_b = 0,075. La regla **no puede derivar** y la revisión **no puede confirmar** sesgo con ventanas de este tamaño: todas las ventanas se liberan y u = 1.

## Consecuencias calculables antes de correr

1. **El Bias Auditor no puede promover con la regla de P1.** Su acción es siempre la del operador BIO (la regla certificada, DE-6), así que CE_a = CE_0 y %CEA = 0 < %RCE = 25. Además, con 13 ventanas no llega a cerrar un intervalo de 20 ciclos. Se informa; cómo evoluciona un rol que no decide es una pregunta para la dirección.
2. **El Explainer no ve decisiones derivadas** (tipo «deriva»), porque el Auditor no puede derivar (punto anterior).
3. **Matcher del equipo:** sus celdas incluyen las Si de perfiles parciales o fallidos (regla 8); su precisión en el equipo no es comparable con la de P1.

## Qué produce P4

- `p4_traza_<caso>.md` y `.html` para los casos pre-registrados: BIO-041, TBO-081, WIO-081 (primer caso de la última ventana de cada escenario). Una tabla por rol: situación inicial, candidatas y acción, situación final, P, K y U, región en que se registró y estado del agente.
- `p4_equipo.ttl` (ABox del equipo), `p4_shacl.txt` (conforme o no, con ΣP = K), `p4_sparql.md` (genealogía de una teoría, teorías que intervinieron en una decisión, teorías por rol y estado, resultado favorable por rol y grupo) y `p4_equipo.json`.

