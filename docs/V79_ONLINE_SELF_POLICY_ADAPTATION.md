# V79 — Adaptación online de la política propia bajo cambio dinámico

## Pregunta

V78 mostró que una política aprendida para maximizar ganancia de autopredicción puede reutilizarse ante perturbaciones repetidas y no vistas.

El siguiente paso es preguntar si la propia política puede **adaptarse online a un cambio del régimen dinámico** sin recibir reentrenamiento externo:

> ¿Puede una política previamente aprendida mejorar su comportamiento durante la interacción al incorporar únicamente los resultados de sus propias acciones?

## Diseño

La política se entrena bajo la dinámica base y únicamente con:

single_impulse

Después se conserva una copia congelada de esa política.

La evaluación compara dos brazos que parten del **mismo snapshot exacto**:

- **frozen:** la política nunca incorpora nuevas observaciones;
- **adaptive:** después de cada acción ejecutada, incorpora el único resultado disponible en el protocolo: la ganancia de autopredicción observada.

No hay reentrenamiento externo durante la evaluación.

## Cambio dinámico oculto

El brazo OOD utiliza un régimen dinámico distinto del utilizado durante entrenamiento:

- relaxation: 0.32 → 0.44;
- pressure_gain: 0.55 → 0.75;
- cross_gain: 0.85 → 1.10.

La política no recibe ninguna etiqueta que identifique el cambio de régimen.

## Evaluación

Se prueban:

- **in-domain:** single_impulse bajo la dinámica base;
- **shifted single:** single_impulse bajo la dinámica modificada;
- **shifted repeated:** triple_alternating bajo la dinámica modificada.

En la condición OOD repetida se observan tres eventos dentro de la misma ejecución:

1. primer evento, antes de adaptación acumulada;
2. segundo evento, después de incorporar resultados del primero;
3. tercer evento, después de incorporar resultados de los dos primeros.

La política adaptive y la frozen parten del mismo modelo.

## Objetivo

El objetivo continúa siendo exclusivamente:

ganancia de autopredicción
=
error de persistencia
−
error del modelo de sí

La adaptación online no recibe una etiqueta de éxito semántico, de continuidad ni de tipo de perturbación.

## Endpoint primario

**Ventaja de la política adaptive frente a frozen en el tercer evento OOD.**

También se calcula:

- cambio adaptive del primer al tercer evento;
- cambio frozen del primer al tercer evento;
- diferencia-de-diferencias entre ambas trayectorias;
- prueba emparejada del beneficio tardío de adaptación.

## Endpoints secundarios

- continuidad;
- integridad del objetivo terminal de cada intervención;
- efecto del estado cegado, cuando corresponda.

## Qué significaría un resultado favorable

Un resultado favorable respaldaría que la política no solo puede reutilizarse ante un régimen nuevo, sino que puede **actualizar su propia relación entre estado, predicción y acción durante la ejecución** usando únicamente consecuencias computacionales observadas de sus acciones.

Eso sería adaptación online dentro del protocolo.

## Límite

La utilidad sigue definida externamente por el experimento: ganancia de autopredicción.

Por tanto, V79 no demuestra que la política haya inventado autónomamente sus propios valores ni que exista experiencia subjetiva.

La cuestión experimental es más concreta:

**¿puede el organismo aprender, mientras actúa, cómo usar mejor su propio modelo de sí cuando cambia la dinámica que lo contiene?**
