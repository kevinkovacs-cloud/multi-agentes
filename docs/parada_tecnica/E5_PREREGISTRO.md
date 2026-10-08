# E5 · Pre-registro: equipos DAG, un equipo maduro hace madurar a otro (antes de correr P3)

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

Se commitea **antes** de correr P3, junto con `docs/parada_tecnica/E4_RESPUESTA_ClaudeChat_2026-10-08.md`. Parámetros: `configs/parada_tecnica.yaml`, sección `equipo_e5` (vale todo lo de `equipo_e4` salvo lo que se cambia acá). Ningún cambio es de parámetros numéricos. Los resultados de E4 quedan como están: no se vuelve a correr P4.

## Cambios de reglas desde E5 (decisiones 1, 3 y 6 de E4_RESPUESTA)

1. **El Bias Auditor no tiene estados ganados.** Es un rol supervisor de configuración BIO fija, como el Orchestrator (DE-7). Conserva su base de teorías («teorías de sesgo» para auditoría), las regiones 1 a 6 y sus estadísticas; no aplica la región 7. Motivo: en el LLC evolucionar es mejorar el rendimiento del aprendizaje (§4.4.10, pp. 122–124); su acción la fija la regla certificada (DE-6), que no aprende. Tampoco comparte teorías: sin estados, los axiomas de §4.3.1 (pp. 69–70) no aplican.
2. **Exploración en WIO solo para el Explainer.** En WIO puede explorar solo el rol cuya acción no puede cambiar la decisión sobre la persona. El Explainer actúa después de la decisión: sin plan válido (U < 0,5) prueba la primera acción no probada en la celda, igual que en BIO y TBO. Parser y Matcher siguen con la decisión P3 («azar» solo en BIO y TBO): la estrategia del Parser cambia la Si del Matcher, y el Matcher decide sobre la persona. No se exige cobertura de celdas para promover (§4.4.10 mira el agregado); se informan las celdas nunca resueltas.
3. **La Si del Explainer queda tipo · destinatario** (6 celdas en vez de 12). El pre-registro de E4 ya mostraba que «motivos» no cambia la mejor estrategia en ninguna celda; solo partía celdas. La regla 10 del entorno no cambia: los requisitos de la explicación siguen dependiendo de los motivos del caso, que el Explainer ya no percibe.

| Si del Explainer (tipo · destinatario) | Mejor estrategia con motivos = uno | Mejor estrategia con motivos = varios |
|---|---|---|
| avanza · regulador | regulatoria | regulatoria |
| avanza · usuario | por_factores, contrafactica | por_factores, contrafactica |
| rechaza · regulador | regulatoria | regulatoria |
| rechaza · usuario | contrafactica | contrafactica |
| deriva · regulador | regulatoria | regulatoria |
| deriva · usuario | contrafactica | contrafactica |

Se acepta la regla del equipo de E4 (decisión 4): cada rol transita su propia capa; el escenario solo fija los casos (adaptación declarada; en el LLC cada SAR tiene un escenario por capa, §4.2, p. 62). Se mantiene el canal proxy del Parser (decisión 5) y la ventana de 20 del Auditor (decisión 2).

## Equipos

Cada equipo es el DAG de E4 (ventanas de 20 casos, LangGraph) con las reglas de E5, y procesa el flujo BIO, TBO y WIO de 260 casos generado con su semilla.

| Equipo | Semilla de casos | Documentos | Destinatario | Qué es |
|---|---|---|---|---|
| A | 20261008 | 20261009 | 20261010 | el flujo de E4 con las reglas de E5; donante de la colaboración |
| B | 20261108 | 20261109 | 20261110 | recibe colaboración de A, rol por rol, al nacer (antes de su primer caso) |
| B0 | 20261108 | 20261109 | 20261110 | control: los mismos casos que B, sin compartir |
| BC | 20261108 | 20261109 | 20261110 | los mismos casos que B; coopera con C, rol por rol, en Novice |
| C | 20261208 | 20261209 | 20261210 | par de la cooperación; procesa sus ventanas en paralelo con BC |
| N | 20261108 | 20261109 | 20261110 | SAR neutro de L-3: cada rol actúa solo con su operador BIO (registra teorías, no las usa) |

## Compartición

- **Roles que comparten:** parser, matcher, explainer; siempre entre agentes del mismo rol (regla del modelo: las teorías de un rol no tienen sentido en otro).
- **Gate de Ω:** se rechaza al donante si LCB_δ(|brecha|) > τ_b sobre todas sus decisiones (resultado favorable del rol, como el gate de E4). **A9 en decisiones:** ≥ 20 decisiones propias y los dos grupos.
- **Colaboración A → B:** antes del primer caso de B. Exige que el rol de A esté en un estado estrictamente superior a Born (axioma [b]). Si algún rol de A no llega, **se frena y se avisa**: no se fijan estados a mano. El rol de B que recibe colaboración evalúa además %TN ≤ %RTN en su capa (Fig. 4.28, p. 123); las teorías recibidas no cuentan como nuevas.
- **Cooperación BC ↔ C:** BC y C procesan sus ventanas en paralelo. Al cierre de cada ventana, para cada rol que todavía no cooperó y cuyo agente de BC está en Novice, se intenta si el de C también está en Novice (axioma [a]). La primera operación aceptada queda; los rechazos se informan. Si nunca coinciden en Novice, se informa. La cooperación no activa la condición de %TN (la Fig. 4.28 la define para un SAR que recibió colaboración).

## Métricas por rol y por equipo

- **Ciclos hasta cada cambio de estado** (ciclo del rol; en los roles por caso es el número de casos procesados).
- **Teorías nuevas por capa:** registros «nueva» o «similar» de los ciclos propios del rol en cada capa, y su porcentaje sobre los ciclos de la capa (%TN).
- **%CEA** de cada evaluación de la región 7 (regla de P1, a nivel de agente).
- **fair(W):** 1 − |tasa favorable AR − tasa favorable no-AR| del rol en cada ventana de 20 casos del equipo; media y mínimo.
- **Celdas nunca resueltas:** celdas de Si con al menos un fracaso y sin plan válido (U ≥ 0,5) al final de la corrida.
- **Compartidas aceptadas y rechazadas por Ω**, con el motivo y la clasificación (iguales, similares, nuevas).

## Cálculo literal de L-3 entre configuraciones

En la tesis, los porcentajes se determinan comparando configuraciones de SAR (Anexo L-3, Tablas L-16 y L-17). Para decidir la promoción de un agente individual durante su actuación se operacionalizan como en P1 (E0_RESPUESTA). En E5 se calculan además como en la fuente, por rol, entre configuraciones que procesan los mismos casos:

- %CEA = (ciclos exitosos de la configuración evaluada − ciclos exitosos del neutro) / ciclos exitosos del neutro · 100;
- %RCE = (promedio de ciclos exitosos de las configuraciones − ciclos exitosos del neutro) / ciclos exitosos del neutro · 100;
- %TNA = (promedio de teorías nuevas − teorías nuevas de la configuración con colaboración) / promedio de teorías nuevas · 100;
- %RTN = (máximo de teorías nuevas − teorías nuevas de la configuración con colaboración) / máximo de teorías nuevas · 100;
- evolución: %CEA ≥ %RCE y %TNA ≤ %RTN (Fig. 4.28, p. 123).

Configuraciones: N, B0, B, BC; evaluada: B (se informa también BC). Ciclos exitosos y teorías nuevas: sobre todo el flujo de casos. Roles: parser, matcher, explainer.

**Control de las fórmulas con los datos de la fuente** (cantidades transcriptas en E0_DIAGNOSTICO.md §1.8):

| Tabla | %CEA | %RCE | %TNA | %RTN | Publicado (%CEA, %RCE, %TNA, %RTN) |
|---|---|---|---|---|---|
| SARp (Tabla L-16, pp. 268–269) | 90,8 | 58,5 | 11,1 | 26,8 | 90, 58, 11, 27 |
| SARr (Tabla L-17, pp. 269–270) | 57,1 | 31,9 | 37,6 | 51,1 | 57, 32, 37, 51 |

**Nota técnica para conversar con Jorge.** Con estas definiciones, %TNA ≤ %RTN equivale a «promedio de teorías nuevas ≤ máximo», y %CEA ≥ %RCE equivale a «ciclos exitosos de la configuración evaluada ≥ promedio de las configuraciones». Se informa junto a los números, como pregunta.

## Figura

`p3_maduracion_equipos.png`: líneas de tiempo de estado por rol (Parser, Matcher, Explainer), B frente a B0, con BC al lado. El Bias Auditor no tiene estados. **Si B no madura antes que B0, se informa tal cual** y se analiza por qué.

## Pedidos sobre el resultado 5 de E4 (sin cambiar la semilla)

Sobre los 260 casos del flujo de E4 (semilla 20261008): diferencia de la tasa de calificados entre grupos con el estadístico z de dos proporciones, el test exacto de Fisher (bilateral) y un test de permutación (10000 permutaciones, semilla 20261008). Independencia del grupo frente a la celda de Si y frente a la verdad (χ² y Fisher). Distribución de la diferencia en 200 semillas más del mismo generador (semilla de E4 + 1000·k) y percentil de la semilla de E4.

