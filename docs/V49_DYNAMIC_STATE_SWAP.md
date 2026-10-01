# V49 — Intervención emparejada del estado dinámico

## Pregunta

¿Cambia el organismo persistente su respuesta ante la misma sonda cuando cambia la coordenada almacenada del estado dinámico mientras la memoria persistente y el resto del estado del receptor permanecen fijos?

## Intervención

Se crean dos bases de datos receptoras idénticas byte por byte.

- DYNAMIC_LOW: dynamic_state = -0.8
- DYNAMIC_HIGH: dynamic_state = +0.8

Solo se interviene la coordenada almacenada `dynamic_state`. La distancia al atractor derivada se recalcula de forma consistente; memoria, presión, cantidad de pasos dinámicos, flujo de eventos, modelo de sí, último pensamiento y contenido de memoria permanecen fijos.

El contexto utiliza event_limit=0 y memory_limit=1.

## Interpretación

Un cambio de elección bajo la intervención emparejada es evidencia de que el estado dinámico numérico expuesto por la arquitectura del organismo influye causalmente sobre la respuesta probada.

Esto no establece consciencia ni experiencia subjetiva.
