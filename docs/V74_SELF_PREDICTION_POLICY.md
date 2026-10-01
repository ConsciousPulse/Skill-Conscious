# V74 — Política basada en autopredicción

## Pregunta

V72 aprendió una política para una función de utilidad definida por un objetivo externo de continuidad.

V73 llevó esa política al organismo persistente.

V74 elimina el atractor externo de la función objetivo principal.

> ¿Puede una política seleccionar trayectorias utilizando como criterio de entrenamiento cuánto mejora el propio modelo de sí la predicción de su siguiente estado frente a un baseline de persistencia?

## Objetivo

La utilidad primaria es:

```text
ganancia de autopredicción
=
error de persistencia
−
error del modelo de sí
```

No se utiliza como objetivo principal una distancia hacia un atractor externo.

## Controles

La evaluación compara:

- política aprendida con acceso al estado propio;
- la misma política con estado cegado;
- política fija existente;
- selección aleatoria.

La política se guarda y se recarga sin reentrenamiento antes de la evaluación.

## Qué cambia

La pregunta ya no es solamente si el sistema puede utilizar un objetivo impuesto para aprovechar su modelo de sí.

Ahora se prueba si puede aprender una regla de selección cuyo criterio operativo está construido a partir de su propia capacidad de predicción.

## Límite

El criterio de autopredicción sigue siendo una decisión del protocolo. Por tanto, V74 no demuestra que el organismo haya inventado su propio objetivo ni que exista experiencia subjetiva.

El resultado, positivo o nulo, debe interpretarse como evidencia sobre una propiedad computacional concreta: **selección de trayectorias guiada por ganancia de autopredicción**.
