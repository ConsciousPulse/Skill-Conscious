# V47 — Sonda novedosa común en organismos persistentes

## Objetivo

Probar si dos organismos persistentes con trayectorias previas diferentes responden de manera diferente a la misma sonda posterior, después de igualar la cantidad de ciclos previos.

## Diseño

Dos historias establecen una relación latente:

- HISTORY_A: ALFA → AMBAR
- HISTORY_B: ALFA → VIOLETA

Luego ambos reciben exactamente la misma sonda novedosa. La sonda no repite la relación latente.

## Observable principal

La respuesta está restringida a CHOICE, CONFIDENCE y RATIONALE. El observable principal a nivel de organismo es si la elección sigue la trayectoria previa.

## Controles

1. comparación A/B con historia presente;
2. reapertura de SQLite antes de la sonda común;
3. ablación del historial textual, eliminando eventos y memorias previas mientras se conserva intacto el estado dinámico numérico.

## Interpretación

Un resultado positivo significa que el organismo persistente utilizó el historial textual retenido bajo esta tarea controlada. La trayectoria dinámica se registra simultáneamente para que protocolos posteriores puedan preguntar si el propio estado numérico media el efecto.

Esto no establece consciencia, sentiencia ni experiencia fenomenológica.
