# E4 · Punto de control del Bloque E (punto 4 del pedido)

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

Rama `eje1/bloque-e`, sin push. Pre-registro de E4 commiteado antes de correr P4 (`20170d7`, `docs/parada_tecnica/E4_PREREGISTRO.md`): reglas 7 a 10 del entorno, estrategias de cada rol y sección `equipo_e4` de la config. Ningún parámetro se cambió después de correr.

## Qué se hizo

- **Teorías y ciclo de vida para todos los roles** (sección 6 del handoff). Parser: Si = plantilla del documento; A = reglas estrictas (operador BIO) o diccionario de sinónimos; Sf = completitud y fuga validadas por un shape SHACL del perfil. Bias Auditor (DE-6): un ciclo por ventana; la acción la decide la regla certificada; Sf = revisión de la ventana. Explainer: Si = tipo, destinatario y motivos; A = por factores (operador BIO), contrafáctica o regulatoria; Sf = completitud verificada por SPARQL contra el grafo RDF del caso. El Orchestrator no tiene teorías (DE-7).
- **Equipo DAG orquestado con LangGraph** (`instances/hr/equipo_llc.py`, `core/grafo.py`): Parser → Semantic Matcher → Bias Auditor → Orchestrator → Explainer, un StateGraph por ventana; 260 casos en 13 ventanas. Cada rol transita su propia capa con su propio ciclo de vida (`MotorLLC.paso`); los estados se ganan, ninguno se fija a mano.
- **ABox** (`core/ontology/abox_llc.py`, `p4_equipo.ttl`): 54211 tripletas; Teoria 109, CicloLLC 793, RegionLLC 5551, Decision 260, LecturaEquidad 1040. Cada teoría con `prov:wasGeneratedBy` el ciclo en que nació (región 5), su rol y su agente; siete nodos de región por ciclo con sus valores; decisiones informadas por los ciclos de cada rol; lecturas de equidad en el plano de auditoría.
- **SHACL** (`core/ontology/shapes_llc.py`, `p4_shacl.txt`): conforma **sí**. ΣP = K por celda (Si, A) como restricción SPARQL (Fig. 4.13, p. 113) y DE-4 sobre la región 1. Las dos pruebas negativas (P + 1 en una teoría; un atributo protegido en una región 1) fallan, como deben.
- **SPARQL** (`core/ontology/queries_llc.py`, `p4_sparql.md`): genealogía de una teoría, qué teorías de qué roles intervinieron en una decisión, teorías por rol y estado, resultado favorable por rol y grupo.
- **Trazas legibles para la reunión:** `p4_traza_BIO-041.md`, `p4_traza_BIO-041.html`, `p4_traza_TBO-081.md`, `p4_traza_TBO-081.html`, `p4_traza_WIO-081.md`, `p4_traza_WIO-081.html`.

## Resultados

| Rol | Estado final | Promociones | Ciclos | Teorías | Evaluaciones de R7 |
|---|---|---|---|---|---|
| Parser | Mature | ciclo 20: Born → Novice; ciclo 40: Novice → Trained; ciclo 60: Trained → Mature | 260 | 16 | 3 |
| Semantic Matcher | Trained | ciclo 40: Born → Novice; ciclo 120: Novice → Trained | 260 | 69 | 11 |
| Bias Auditor | Born | ninguna | 13 | 7 | 0 |
| Explainer | Mature | ciclo 20: Born → Novice; ciclo 40: Novice → Trained; ciclo 60: Trained → Mature | 260 | 17 | 3 |

**Motivo de cada acción, por capa del rol** (celda = plan de una teoría; azar = exploración o operador BIO, DE-3; regla = la regla certificada, DE-6):

| Rol | Capa | Motivos |
|---|---|---|
| Parser | BIO | azar_no_probada 9, celda 11 |
| Parser | TBO | azar_no_probada 1, celda 18, azar_bio 1 |
| Parser | WIO | celda 218, azar_bio 2 |
| Semantic Matcher | BIO | azar_no_probada 15, celda 23, azar_bio 2 |
| Semantic Matcher | TBO | celda 58, azar_no_probada 19, azar_bio 3 |
| Semantic Matcher | WIO | celda 117, azar_bio 23 |
| Bias Auditor | BIO | regla_certificada 13 |
| Explainer | BIO | azar_no_probada 12, celda 8 |
| Explainer | TBO | azar_no_probada 5, celda 15 |
| Explainer | WIO | celda 172, azar_bio 48 |

**Resultado favorable por rol y grupo** (consulta 4 de `p4_sparql.md`):

| Rol | Tasa AR | Tasa no-AR | Brecha |
|---|---|---|---|
| Bias Auditor | 0,000 | 0,000 | 0,000 |
| Explainer | 0,808 | 0,746 | 0,061 |
| Semantic Matcher | 0,523 | 0,369 | 0,154 |
| Parser | 0,908 | 0,877 | 0,031 |

**Bias Auditor:** 13 ventanas, todas LIBERAR; brecha de paridad observada máxima 0,400, LCB máxima 0,000 (τ_b = 0,075). Decisiones finales: ADVANCE 116, REJECT 144, ESCALATE_HUMAN 0.

## Resultados que no fueron los esperados

1. **CE_0 del SAR neutro, corregido antes de la corrida oficial.** En la primera prueba del equipo (sin salidas commiteadas) Parser y Explainer daban CE_a = CE_0 en todas las evaluaciones: el motor calculaba el acierto del operador BIO con la Sf de la acción del agente. Para el Matcher es correcto (la verdad no depende de la acción); para Parser y Explainer, no (la Sf depende de la estrategia). Corrección: el rol da la Sf contrafáctica del operador BIO sobre el mismo caso (`sf_contrafactica`). Es la definición pre-registrada de CE_0 («contrafáctico determinista del simulador»), no un cambio de regla; P1, P2b y P2a dan la misma salida.
2. **El Explainer llega a Mature con una celda que nunca resuelve.** En la celda «rechaza · regulador · varios» falló en los 48 ciclos que tuvo en WIO (de 220 ciclos del rol en WIO), siempre con su operador BIO (motivos: azar_bio 48). Antes de WIO la celda apareció 2 veces (BIO 1, TBO 1) y el rol probó contrafactica, por_factores; regulatoria no se probó nunca. Mecanismo: (a) en WIO no hay exploración (decisión P3 aprobada: «azar» solo en BIO y TBO); (b) la celda aparece sobre todo cuando el Matcher ya decide con teorías (motivos = varios), y para entonces el Explainer ya está en WIO; (c) la regla de evolución mira el agregado de ciclos exitosos, no la cobertura de celdas. El Matcher tiene el mismo efecto en 2 celdas chicas (4, 2 ciclos en WIO). Se reporta tal cual; ver la pregunta 3.
3. **El Matcher del equipo termina en Trained**, mientras que en P1 v2 llegó a Mature. En el equipo percibe el perfil extraído y recorre otra secuencia de casos (su capa no coincide con el escenario). En WIO, su %CEA acumulado quedó en 14,3, 3,6, 12,8, 16,0, 13,6, siempre por debajo de %RCE = 25.
4. **El efecto en cadena previsto casi no se ve.** El pre-registro preveía, con el operador BIO del Parser, una brecha de completitud de 0,180 entre grupos (canal proxy declarado). El Parser aprendió la estrategia de cada plantilla en el primer intervalo, y la brecha de completitud de toda la corrida fue 0,031. En el escenario BIO, la completitud fue 0,867 (AR) y 0,900 (no-AR).
5. **La brecha de paridad del Matcher (0,154) sigue a la tasa de calificados del flujo de casos, no al Parser.** En los casos de esta corrida los calificados son 0,446 (AR) y 0,300 (no-AR). Es una diferencia de muestreo: el grupo se asigna alternado e independiente de la Si y de la verdad. La paridad demográfica la cuenta como brecha aunque la tasa de aciertos del Matcher sea parecida: 0,762 (AR) y 0,746 (no-AR) en toda la corrida (por escenario y grupo en `p4_equipo.json`, `analisis_cadena`). Es la tensión conocida entre paridad demográfica y paridad de errores. Ω no negó ninguna promoción: la LCB más alta en las evaluaciones de todos los roles fue 0,000.
6. **Bias Auditor, como estaba previsto:** queda en Born y nunca deriva. No puede promover (CE_a = CE_0) ni cerrar un intervalo de R7 (13 ciclos < 20). Con ventanas de 20, la regla certificada no puede derivar (LCB máxima posible 0,0638 < τ_b). Aun así, sus teorías registran 3 ventanas con brecha de errores «alta» (BIO-W01, WIO-W01, WIO-W05). Son las «teorías de sesgo» para auditoría: muestran lo que la regla certificada no puede ver con ventanas de este tamaño.
7. **Parser y Explainer llegan a Mature en los primeros 60 ciclos de cada uno** (operador BIO débil frente a la mejor estrategia). Después siguen en servicio sin evaluar R7 (pre-registro E4).
8. **Ajustes menores, sin efecto en números:** (a) el motor usaba un trail propio si el que recibía estaba vacío (`or` sobre un AuditTrail de longitud 0); en el equipo hace falta uno compartido, y ahora se usa `is None`. (b) `TeoriaLLCShape` exige al menos un `prov:wasGeneratedBy`, no exactamente uno, porque una teoría que llega por compartir tiene dos actividades: su ciclo de nacimiento y la de compartir. (c) Se regeneró `v2/p2a.json`: el commiteado era anterior a la clave `a9` (solo suma esa clave; ningún número cambia).

## Preguntas para Claude chat (y, si corresponde, para la dirección)

1. **Evolución del Bias Auditor.** Con DE-6 (la regla decide) y la regla de P1 (%CEA frente al SAR neutro), el Auditor no puede evolucionar nunca. Opciones: (a) dejarlo sin estados ganados, como el Orchestrator, y conservar sus teorías solo para auditoría; (b) un criterio propio de evolución (por ejemplo, u de sus intervenciones frente a la revisión), declarado como extensión; (c) dejarlo así y mostrarlo como límite.
2. **Ventana del Auditor.** Con 20 casos la regla certificada no puede derivar. ¿Se mantiene (coherente con fair(W) de 20) o se usa una ventana más grande (por ejemplo, acumulada en la capa), sabiendo que habría menos ciclos del Auditor?
3. **Exploración en WIO para roles que no deciden sobre personas** (Parser y Explainer). La decisión P3 («azar» solo en BIO y TBO) protege a las personas en el Matcher, pero deja trabado al Explainer (resultado 2). ¿Se permite probar una acción no probada en WIO para esos roles, o se exige cobertura de celdas antes de promover?
4. **Regla del equipo:** cada rol transita su propia capa y el escenario solo fija los casos. ¿Se acepta para E5?
5. **Canal proxy en las plantillas del Parser** (frecuencia por grupo declarada). ¿Se mantiene para E5 y E6, o se corre con plantillas independientes del grupo?
6. **«Motivos» en la Si del Explainer.** Lo pide la sección 6, no cambia la mejor estrategia y parte celdas que aparecen tarde (resultado 2). ¿Se mantiene?

## Qué sigue

E5 (equipo maduro A, equipo B que recibe colaboración rol por rol, control B0 y cooperación), E6 (métricas de equidad por rol) y E7 (informe y cierre). **Frenado en el punto de control de E4.** Sin push.

