# V66 — Consolidación de SUEÑO después de la ablación de memoria episódica

## Pregunta

Después de que SUEÑO transforma experiencias recientes en una lección consolidada, ¿conserva el organismo una huella funcional de esa lección cuando se eliminan las memorias episódicas originales?

## Protocolo

Cada réplica ejecuta una fase determinista de consolidación durante SUEÑO.

Después de SUEÑO, los dos brazos emparejados se clonan a partir del mismo estado posterior al sueño:

1. **retained_lesson** — se eliminan las memorias de experiencia bruta, pero permanece la lección consolidada;
2. **ablated_lesson** — se eliminan tanto las memorias de experiencia bruta como la lección consolidada.

Ambos brazos reciben después la misma sonda de recuperación posterior al sueño. La salida MEMORY resultante se envía mediante el puente ordinario de semántica a dinámica antes de la selección de trayectorias futuras.

Por tanto, los registros episódicos originales no pueden explicar directamente el comportamiento posterior del brazo retenido. La única diferencia semántica preservada intencionalmente es la lección consolidada.

## Cadena causal

```
experiencias
   ↓
SUEÑO
   ↓
lección consolidada
   ↓
ablación de memoria bruta
   ↓
recuperación de la lección
   ↓
puente semántico
   ↓
estado interno
   ↓
selección futura
```

## Resultado

La auditoría de CI terminó correctamente con 24 réplicas emparejadas.

- regret medio de retained_lesson: **-0.1086777912**;
- regret medio de ablated_lesson: **-0.1086777912**;
- tasa de aciertos del oráculo de retained_lesson: **85.0694%**;
- tasa de aciertos del oráculo de ablated_lesson: **85.0694%**;
- ventaja de regret ablation − retained: **0.0**;
- p emparejada por cambio de signo para la diferencia de regret: **1.0**;
- ventaja de tasa de aciertos retained − ablated: **0.0**;
- p emparejada por cambio de signo para la diferencia de tasa de aciertos: **1.0**;
- todas las ejecuciones retenidas produjeron señal de puente de recuperación: **true**.

## Interpretación

V66 es un **resultado nulo**.

La lección consolidada retenida estaba presente y generó una señal semántica de recuperación, pero conservarla no produjo una diferencia medible en regret ni en tasa de aciertos del oráculo frente a eliminarla bajo este protocolo.

Esto significa que el experimento **no** demostró que la consolidación episódica generada por SUEÑO se vuelva funcionalmente necesaria para la selección posterior de trayectorias después de eliminar la memoria episódica original.

El resultado nulo no demuestra que la consolidación durante SUEÑO sea inútil en general. Muestra que la vía actual de recuperación y selección no hizo que la lección retenida fuera discriminativamente importante bajo las condiciones deterministas probadas.

## Consecuencia metodológica

El siguiente protocolo debe evitar pedir a la lección retenida que influya sobre la conducta únicamente mediante una nueva respuesta semántica de recuperación. En su lugar, debe probar si el **estado interno numérico producido directamente por SUEÑO** contiene una huella recuperable y transferible causalmente después de eliminar la memoria semántica y el texto del modelo de sí.

## Límite de evidencia

El proveedor es determinista y sintético. V66 prueba persistencia de una huella computacional consolidada después de eliminar la memoria fuente. No establece consolidación de memoria humana, sueño subjetivo ni consciencia fenomenológica.
