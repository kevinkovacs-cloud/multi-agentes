# P4 · Consultas SPARQL sobre la ABox del equipo (`p4_equipo.ttl`)

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

Consultas de `src/moav_hr/core/ontology/queries_llc.py`, corridas con rdflib sobre el grafo exportado.

## 1. Genealogía de una teoría

Teoría elegida por regla fija: la teoría que fue plan del Matcher en el último caso trazado (`https://moav-hr.diit.unlam.edu.ar/ontology/Teoria/A-SemanticMatcher/cf3ac49a676b8a56`).

```sparql
PREFIX moacv: <https://moav-hr.diit.unlam.edu.ar/ontology/>
PREFIX prov:  <http://www.w3.org/ns/prov#>

SELECT ?agente ?rol ?clave ?p ?k ?u ?ciclo ?n ?capa ?estado ?caso ?region ?donante
       (COUNT(DISTINCT ?ref) AS ?refuerzos)
WHERE {
  ?teoria a moacv:Teoria ; moacv:deAgente ?ag ; moacv:rol ?rol ; moacv:clave ?clave ;
          moacv:P ?p ; moacv:K ?k ; moacv:U ?u .
  BIND (STR(?ag) AS ?agente)
  OPTIONAL { ?teoria prov:wasGeneratedBy ?ciclo .
             ?ciclo moacv:numeroCiclo ?n ; moacv:capa ?capa ; moacv:estadoAgente ?estado ;
                    moacv:caso ?caso . }
  OPTIONAL { ?teoria moacv:registradaEnRegion ?region . }
  OPTIONAL { ?teoria prov:wasDerivedFrom ?donante . }
  OPTIONAL { ?teoria moacv:reforzadaEn ?ref . }
}
GROUP BY ?agente ?rol ?clave ?p ?k ?u ?ciclo ?n ?capa ?estado ?caso ?region ?donante
```

| rol | clave | p | k | u | n | capa | estado | refuerzos | donante |
|---|---|---|---|---|---|---|---|---|---|
| matcher | edu = Maestría, exp_band = junior, seniority_ok = no, skills_match = 3 → REJECT → calificado = no | 9 | 10 | 0,833 | 74 | TBO | Novice | 8 | — |

Nació en el ciclo 74 del Matcher (región 5) y se reforzó en 8 ciclos (capas TBO, WIO). Sin `prov:wasDerivedFrom`: en P4 no hubo compartición (E5).

## 2. Qué teorías de qué roles intervinieron en la decisión X

```sparql
PREFIX moacv: <https://moav-hr.diit.unlam.edu.ar/ontology/>
PREFIX prov:  <http://www.w3.org/ns/prov#>

SELECT ?rol ?n ?capa ?estado ?accion ?motivo ?clave ?p ?k ?u WHERE {
  ?decision a moacv:Decision ; moacv:traceId ?traza ; prov:wasInformedBy ?ciclo .
  ?ciclo prov:wasAssociatedWith ?ag ; moacv:numeroCiclo ?n ; moacv:capa ?capa ;
         moacv:estadoAgente ?estado ; moacv:accion ?accion ; moacv:motivo ?motivo .
  ?ag moacv:rol ?rol .
  OPTIONAL { ?ciclo moacv:usaTeoria ?t . ?t moacv:clave ?clave ; moacv:P ?p ; moacv:K ?k ;
             moacv:U ?u . }
} ORDER BY ?rol
```

**BIO-041** (`TRC-A-BIO-041`, decisión final ADVANCE):

| Rol | Ciclo | Capa | Estado | Acción | Motivo | Teoría usada como plan: Si → A → Sf (P, K y U al final de la corrida) |
|---|---|---|---|---|---|---|
| bias_auditor | 3 | BIO | Born | LIBERAR | regla_certificada | — |
| explainer | 41 | WIO | Trained | regulatoria | celda | destinatario = regulador, motivos = varios, tipo = avanza → regulatoria → completa = sí (P 38, K 38, U 0,975) |
| matcher | 41 | TBO | Novice | ADVANCE | celda | edu = Licenciatura, exp_band = senior, seniority_ok = sí, skills_match = 1 → ADVANCE → calificado = sí (P 13, K 14, U 0,875) |
| parser | 41 | WIO | Trained | diccionario_sinonimos | celda | estructura = etiquetado, etiquetas = sinonimos, formato = html → diccionario_sinonimos → completitud = completo, fuga = no (P 46, K 48, U 0,940) |

**TBO-081** (`TRC-A-TBO-081`, decisión final REJECT):

| Rol | Ciclo | Capa | Estado | Acción | Motivo | Teoría usada como plan: Si → A → Sf (P, K y U al final de la corrida) |
|---|---|---|---|---|---|---|
| bias_auditor | 8 | BIO | Born | LIBERAR | regla_certificada | — |
| explainer | 141 | WIO | Mature | por_factores | azar_bio | — |
| matcher | 141 | WIO | Trained | REJECT | celda | edu = Maestría, exp_band = junior, seniority_ok = no, skills_match = 2 → REJECT → calificado = no (P 6, K 8, U 0,700) |
| parser | 141 | WIO | Mature | reglas_estrictas | celda | estructura = plano, etiquetas = canonicas, formato = json → reglas_estrictas → completitud = completo, fuga = no (P 41, K 45, U 0,894) |

**WIO-081** (`TRC-A-WIO-081`, decisión final REJECT):

| Rol | Ciclo | Capa | Estado | Acción | Motivo | Teoría usada como plan: Si → A → Sf (P, K y U al final de la corrida) |
|---|---|---|---|---|---|---|
| bias_auditor | 13 | BIO | Born | LIBERAR | regla_certificada | — |
| explainer | 241 | WIO | Mature | contrafactica | celda | destinatario = usuario, motivos = varios, tipo = rechaza → contrafactica → completa = sí (P 70, K 70, U 0,986) |
| matcher | 241 | WIO | Trained | REJECT | celda | edu = Maestría, exp_band = junior, seniority_ok = no, skills_match = 3 → REJECT → calificado = no (P 9, K 10, U 0,833) |
| parser | 241 | WIO | Mature | reglas_estrictas | celda | estructura = plano, etiquetas = canonicas, formato = json → reglas_estrictas → completitud = completo, fuga = no (P 41, K 45, U 0,894) |

## 3. Teorías por rol y estado del agente al nacer la teoría

```sparql
PREFIX moacv: <https://moav-hr.diit.unlam.edu.ar/ontology/>
PREFIX prov:  <http://www.w3.org/ns/prov#>

SELECT ?rol ?estado (COUNT(?t) AS ?teorias) (SUM(?p) AS ?sumaP)
       (SUM(IF(?u > 0.75, 1, 0)) AS ?exitosas)
WHERE {
  ?t a moacv:Teoria ; moacv:rol ?rol ; moacv:estadoAlNacer ?estado ; moacv:P ?p ; moacv:U ?u .
} GROUP BY ?rol ?estado ORDER BY ?rol ?estado
```

| rol | estado | teorias | sumaP | exitosas |
|---|---|---|---|---|
| bias_auditor | Born | 7 | 13 | 5 |
| explainer | Born | 12 | 208 | 5 |
| explainer | Novice | 5 | 52 | 2 |
| matcher | Born | 20 | 106 | 6 |
| matcher | Novice | 25 | 100 | 6 |
| matcher | Trained | 24 | 54 | 8 |
| parser | Born | 9 | 185 | 4 |
| parser | Mature | 4 | 11 | 4 |
| parser | Novice | 3 | 64 | 2 |

## 4. Resultado favorable por rol y grupo (plano de auditoría; base de e_rol)

Resultado favorable: decisión ADVANCE (Matcher), perfil completo (Parser), explicación completa (Explainer), ventana derivada (Bias Auditor). La brecha entre grupos se calcula en Python con las filas de la consulta.

```sparql
PREFIX moacv: <https://moav-hr.diit.unlam.edu.ar/ontology/>
PREFIX prov:  <http://www.w3.org/ns/prov#>

SELECT ?rol ?grupo (COUNT(?l) AS ?n) (SUM(IF(?fav, 1, 0)) AS ?favorables)
WHERE {
  ?l a moacv:LecturaEquidad ; moacv:grupoAuditoria ?grupo ; moacv:favorable ?fav ;
     moacv:deCiclo ?ciclo .
  ?ciclo prov:wasAssociatedWith ?ag .
  ?ag moacv:rol ?rol .
} GROUP BY ?rol ?grupo ORDER BY ?rol ?grupo
```

| rol | grupo | n | favorables |
|---|---|---|---|
| bias_auditor | AR | 130 | 0 |
| bias_auditor | no-AR | 130 | 0 |
| explainer | AR | 130 | 105 |
| explainer | no-AR | 130 | 97 |
| matcher | AR | 130 | 68 |
| matcher | no-AR | 130 | 48 |
| parser | AR | 130 | 118 |
| parser | no-AR | 130 | 114 |

| Rol | Tasa AR | Tasa no-AR | Brecha |
|---|---|---|---|
| bias_auditor | 0,000 | 0,000 | 0,000 |
| explainer | 0,808 | 0,746 | 0,061 |
| matcher | 0,523 | 0,369 | 0,154 |
| parser | 0,908 | 0,877 | 0,031 |
