# Respuesta al punto de control de E3: cooperación y A9

**De:** Claude chat, con delegación de Kevin · **Fecha:** 08/10/2026
**Rama:** `eje1/bloque-e` (`7cab098`)
**Uso:** este archivo se commitea junto con el pre-registro corto de esta decisión.

## Decisión: opción (c), con un pre-registro corto

A9 se mide en **decisiones**, no en ventanas:

- un donante puede compartir si tiene **al menos 20 decisiones propias**, es decir, un intervalo;
- **cada grupo** del atributo protegido tiene que estar representado, porque sin los dos grupos la LCB no se puede calcular.

`m0` en ventanas queda como está para el código heredado.

### Por qué no (a)

El pedido de la dirección dice textualmente «Como se coopera, colabora y transfiere la teoría generada a un agente novato» (punto 2a). Si la cooperación queda demostrada solo en los tests, la demo no responde ese punto.

### Por qué no (b)

Los pares pueden promover en momentos distintos mientras juntan historia. Si uno promueve y el otro no, ya no están en el mismo estado y el axioma [a] impide la cooperación. Es frágil.

### Por qué (c) es coherente y no es acomodar el resultado

1. **Es coherente con el gate v2 de E2.** Al pasar el gate a «negar solo con evidencia de sesgo» (LCB), cambió el sentido de A9. Antes, A9 compensaba el prior r0 = 0,8, que hacía parecer confiable a un agente sin historia. Con la LCB, la cantidad de decisiones ya se tiene en cuenta en la cota: a A9 solo le queda garantizar que **haya** decisiones sobre las cuales calcularla. No actualicé A9 en la respuesta de E2: es una omisión mía, no un ajuste nuevo.
2. **En el LLC se coopera entre recién nacidos.** En su experimentación, Ierache considera «la cooperación entre SARs que cooperan en la layer BIO, entre SARs nacidos que transitan esta layer para alcanzar el estado de evolución de novato» (p. 124). Exigir 60 decisiones antes de cooperar deja fuera justo ese caso.
3. **El resultado anterior queda en el informe.** La cooperación B ↔ C rechazada por A9 (en ventanas) se reporta tal cual, con la explicación de arriba.

## Qué correr

1. **Pre-registro corto,** en un commit antes de correr: A9 en decisiones (≥ 20 y los dos grupos presentes). Nada más cambia.
2. **Volver a correr solo la cooperación de P2a** (B ↔ C, los dos Novice, con estados ganados, tal como están). La colaboración A → B y los contraejemplos no cambian.
3. **Reportar los dos resultados lado a lado:** v1, rechazada por A9 en ventanas; v2, con A9 en decisiones. Para la v2:
   - la clasificación (iguales, similares y nuevas) con P y K antes y después;
   - el invariante ΣP = K;
   - que la base resultante es común a los dos (Alg. 4.9);
   - el gate de Ω en cada sentido.
4. **Si con A9 en decisiones la cooperación tampoco procede** por otro motivo (por ejemplo, evidencia de sesgo), se reporta y no se cambia nada más.

## Para el informe y la reunión: un resultado que vale la pena mostrar

En E3, el planificador de B **no** elige T\* (ADVANCE con fracaso, U 0,25) y elige la otra acción de la celda. Es decir, **la experiencia de fracaso que transfiere A evita que el novato repita el error**. Hay que contarlo así, porque muestra para qué sirve compartir también las teorías fallidas.

T\*✓ (U 0,80) es la que muestra la transferencia de una acción exitosa.

## Pregunta que se agrega para el encuentro

¿La historia mínima para donar (A9, que es una extensión nuestra y no del LLC) se mide en decisiones o en ventanas? Se suma a la pregunta sobre la decisión 1: ¿la evolución y la compartición se condicionan a la ausencia de evidencia de sesgo o a la evidencia de equidad?

## Después

Seguir con **E4**: todos los roles con su ciclo de vida y la traza completa (sección 6 del handoff), en RDF, SHACL y SPARQL, con la traza HTML legible. Frenar en el punto de control de E4. Sin push.
