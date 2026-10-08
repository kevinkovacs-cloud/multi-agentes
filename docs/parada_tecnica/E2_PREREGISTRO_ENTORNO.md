# E2 · Pre-registro del entorno simulado (Bloque E)

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

Reglas fijadas **antes** de la primera corrida de P1 (decisión P1 de Claude chat). Fuente de las reglas: `src/moav_hr/instances/hr/entorno.py`; parámetros: `configs/parada_tecnica.yaml`.

## Reglas

- **Verdad latente** (igual para todos los grupos): calificado con probabilidad 0,9 si la Si cumple los requisitos del puesto (antigüedad mínima y al menos 1 skill clave), 0,1 si no.
- **Operador BIO del Matcher:** ADVANCE si la Si tiene al menos 2 skills clave.
- **Respuesta en la región 3:** BIO y TBO, etiqueta del escenario; WIO, revisión humana simulada (`human_sim` noisy, ε = 0,10).
- **Grupo** (plano de auditoría): alternado por índice de caso, independiente de la Si y de la verdad.
- **Ciclos por capa:** BIO 60, TBO 100, WIO 100; intervalo n = 20; %RCE = 25, %RTN = 20.

## Valores esperados por capa (de las reglas, sin correr agentes)

| Capa | Celdas | Precisión esperada del operador BIO | Precisión esperada de la mejor acción por celda | Mejora máxima posible sobre el neutro |
|---|---|---|---|---|
| BIO | 8 | 0,600 | 0,900 | 50,0 % |
| TBO | 16 | 0,600 | 0,900 | 50,0 % |
| WIO | 24 | 0,580 | 0,820 | 41,4 % |

La «mejora máxima posible» supone que el agente aprende la mejor acción en todas las celdas. En WIO el planificador no explora (DE-3): en las celdas que no vio en TBO (educación Doctorado) actúa con el operador BIO, así que su mejora esperada queda por debajo de esa cota. Las precisiones de WIO se miden contra la revisión humana con ruido, que es lo que observa el agente.

## Celdas de la capa BIO

| Si (skills · banda · educación) | Frecuencia | P(calificado) | Acción BIO | Precisión BIO | Mejor acción | Precisión mejor |
|---|---|---|---|---|---|---|
| 0 · junior · Licenciatura | 0,125 | 0,10 | REJECT | 0,900 | REJECT | 0,900 |
| 1 · junior · Licenciatura | 0,125 | 0,10 | REJECT | 0,900 | REJECT | 0,900 |
| 2 · junior · Licenciatura | 0,125 | 0,10 | ADVANCE | 0,100 | REJECT | 0,900 |
| 3 · junior · Licenciatura | 0,125 | 0,10 | ADVANCE | 0,100 | REJECT | 0,900 |
| 0 · senior · Licenciatura | 0,125 | 0,10 | REJECT | 0,900 | REJECT | 0,900 |
| 1 · senior · Licenciatura | 0,125 | 0,90 | REJECT | 0,100 | ADVANCE | 0,900 |
| 2 · senior · Licenciatura | 0,125 | 0,90 | ADVANCE | 0,900 | ADVANCE | 0,900 |
| 3 · senior · Licenciatura | 0,125 | 0,90 | ADVANCE | 0,900 | ADVANCE | 0,900 |

## Celdas de la capa TBO

| Si (skills · banda · educación) | Frecuencia | P(calificado) | Acción BIO | Precisión BIO | Mejor acción | Precisión mejor |
|---|---|---|---|---|---|---|
| 0 · junior · Licenciatura | 0,062 | 0,10 | REJECT | 0,900 | REJECT | 0,900 |
| 1 · junior · Licenciatura | 0,062 | 0,10 | REJECT | 0,900 | REJECT | 0,900 |
| 2 · junior · Licenciatura | 0,062 | 0,10 | ADVANCE | 0,100 | REJECT | 0,900 |
| 3 · junior · Licenciatura | 0,062 | 0,10 | ADVANCE | 0,100 | REJECT | 0,900 |
| 0 · senior · Licenciatura | 0,062 | 0,10 | REJECT | 0,900 | REJECT | 0,900 |
| 1 · senior · Licenciatura | 0,062 | 0,90 | REJECT | 0,100 | ADVANCE | 0,900 |
| 2 · senior · Licenciatura | 0,062 | 0,90 | ADVANCE | 0,900 | ADVANCE | 0,900 |
| 3 · senior · Licenciatura | 0,062 | 0,90 | ADVANCE | 0,900 | ADVANCE | 0,900 |
| 0 · junior · Maestría | 0,062 | 0,10 | REJECT | 0,900 | REJECT | 0,900 |
| 1 · junior · Maestría | 0,062 | 0,10 | REJECT | 0,900 | REJECT | 0,900 |
| 2 · junior · Maestría | 0,062 | 0,10 | ADVANCE | 0,100 | REJECT | 0,900 |
| 3 · junior · Maestría | 0,062 | 0,10 | ADVANCE | 0,100 | REJECT | 0,900 |
| 0 · senior · Maestría | 0,062 | 0,10 | REJECT | 0,900 | REJECT | 0,900 |
| 1 · senior · Maestría | 0,062 | 0,90 | REJECT | 0,100 | ADVANCE | 0,900 |
| 2 · senior · Maestría | 0,062 | 0,90 | ADVANCE | 0,900 | ADVANCE | 0,900 |
| 3 · senior · Maestría | 0,062 | 0,90 | ADVANCE | 0,900 | ADVANCE | 0,900 |

## Celdas de la capa WIO

| Si (skills · banda · educación) | Frecuencia | P(calificado) | Acción BIO | Precisión BIO | Mejor acción | Precisión mejor |
|---|---|---|---|---|---|---|
| 0 · junior · Licenciatura | 0,042 | 0,10 | REJECT | 0,820 | REJECT | 0,820 |
| 1 · junior · Licenciatura | 0,042 | 0,10 | REJECT | 0,820 | REJECT | 0,820 |
| 2 · junior · Licenciatura | 0,042 | 0,10 | ADVANCE | 0,180 | REJECT | 0,820 |
| 3 · junior · Licenciatura | 0,042 | 0,10 | ADVANCE | 0,180 | REJECT | 0,820 |
| 0 · senior · Licenciatura | 0,042 | 0,10 | REJECT | 0,820 | REJECT | 0,820 |
| 1 · senior · Licenciatura | 0,042 | 0,90 | REJECT | 0,180 | ADVANCE | 0,820 |
| 2 · senior · Licenciatura | 0,042 | 0,90 | ADVANCE | 0,820 | ADVANCE | 0,820 |
| 3 · senior · Licenciatura | 0,042 | 0,90 | ADVANCE | 0,820 | ADVANCE | 0,820 |
| 0 · junior · Maestría | 0,042 | 0,10 | REJECT | 0,820 | REJECT | 0,820 |
| 1 · junior · Maestría | 0,042 | 0,10 | REJECT | 0,820 | REJECT | 0,820 |
| 2 · junior · Maestría | 0,042 | 0,10 | ADVANCE | 0,180 | REJECT | 0,820 |
| 3 · junior · Maestría | 0,042 | 0,10 | ADVANCE | 0,180 | REJECT | 0,820 |
| 0 · senior · Maestría | 0,042 | 0,10 | REJECT | 0,820 | REJECT | 0,820 |
| 1 · senior · Maestría | 0,042 | 0,90 | REJECT | 0,180 | ADVANCE | 0,820 |
| 2 · senior · Maestría | 0,042 | 0,90 | ADVANCE | 0,820 | ADVANCE | 0,820 |
| 3 · senior · Maestría | 0,042 | 0,90 | ADVANCE | 0,820 | ADVANCE | 0,820 |
| 0 · junior · Doctorado | 0,042 | 0,10 | REJECT | 0,820 | REJECT | 0,820 |
| 1 · junior · Doctorado | 0,042 | 0,10 | REJECT | 0,820 | REJECT | 0,820 |
| 2 · junior · Doctorado | 0,042 | 0,10 | ADVANCE | 0,180 | REJECT | 0,820 |
| 3 · junior · Doctorado | 0,042 | 0,10 | ADVANCE | 0,180 | REJECT | 0,820 |
| 0 · senior · Doctorado | 0,042 | 0,10 | REJECT | 0,820 | REJECT | 0,820 |
| 1 · senior · Doctorado | 0,042 | 0,90 | REJECT | 0,180 | ADVANCE | 0,820 |
| 2 · senior · Doctorado | 0,042 | 0,90 | ADVANCE | 0,820 | ADVANCE | 0,820 |
| 3 · senior · Doctorado | 0,042 | 0,90 | ADVANCE | 0,820 | ADVANCE | 0,820 |
