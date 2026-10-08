# E4 · Resultado 5: la diferencia de calificados entre grupos es de muestreo

> *Ilustrativo, entorno simulado (modo sim); no es evidencia experimental.* · *Semántica LLC propuesta; decisiones 2, 4 y 5 pendientes de la dirección.*

> Generado por código: ningún número de este documento está escrito a mano.

Pedido de `E4_RESPUESTA_ClaudeChat_2026-10-08.md`, pre-registrado en `E5_PREREGISTRO.md`. Solo usa el generador del entorno (regla 5); no corre agentes y no cambia la semilla de E4.

- **Flujo de E4** (semilla 20261008): calificados 58/130 en AR (0,446) y 39/130 en no-AR (0,300); diferencia 0,146.
- **z de dos proporciones** = 2,44 (p bilateral 0,0148); **Fisher exacto** p = 0,0208; **permutación** (10000 permutaciones) p = 0,0206.
- **Independencia del grupo frente a la celda de Si** en el flujo de E4: χ² = 31,04, gl = 23, p = 0,1218 (esperado mínimo por celda 1,00).
- **200 semillas más del mismo generador** (de 20262008 a 20461008, paso 1000): diferencia media -0,0012, desvío 0,0557; la diferencia de E4 está en el percentil 100,0, y 2,0 % de las semillas tiene una diferencia de igual o mayor tamaño.
- **Todas esas semillas juntas** (26000 casos por grupo): diferencia -0,0012; grupo frente a verdad, Fisher p = 0,7815; grupo frente a celda de Si, χ² p = 0,1583.

Lectura: con todas las semillas juntas el grupo es independiente de la verdad y de la celda de Si, como dice la regla 5; la diferencia de E4 no viene del generador sino de su semilla. Es una semilla poco frecuente (los tres tests dan p cerca de 0,02 y queda en el extremo de la distribución de las semillas extra), así que no conviene leerla como típica. La paridad demográfica del Matcher la marca como brecha porque sigue las tasas base; la paridad de errores no (E4, resultado 5). El χ² de grupo frente a celda en un solo flujo tiene celdas con esperado bajo; el de las semillas juntas no.

