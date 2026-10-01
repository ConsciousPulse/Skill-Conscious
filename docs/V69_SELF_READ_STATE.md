# V69 — Lectura del estado propio después de la ablación semántica

## Pregunta

Después de eliminar memoria, eventos, snapshots, presión, memoria dinámica y el texto del modelo de sí, ¿un modelo aprendido previamente de la propia dinámica puede leer el estado numérico restante y utilizar esa lectura para seleccionar una trayectoria?

V69 cambia el foco de V68:

```
V68: ¿el estado conserva una diferencia?
V69: ¿la IA puede leer esa diferencia y usarla?
```

## Protocolo

24 réplicas.

Cada réplica genera dos historias:

- **estable** — continuidad y persistencia;
- **frontera** — divergencia y exploración.

Después de SUEÑO se realiza ablación semántica total. El texto del modelo de sí también se elimina.

### Modelo de sí

Se entrena **un único SelfObserver compartido**, con 512 transiciones de dinámica genérica producidas independientemente de las condiciones estable/frontera.

Por diseño, el modelo no recibe las etiquetas de las condiciones experimentales.

### Lectura propia

Se prueban tres señales candidatas:

```
-1   0   +1
```

Para cada candidata, el SelfObserver predice el siguiente estado a partir del estado interno observado.

La política selecciona la señal cuyo estado predicho minimiza el desplazamiento respecto del estado actual. La lectura del estado participa directamente en la decisión.

### Control

Existe un brazo **OFF** en el que las variables de estado se sustituyen por cero antes de consultar el SelfObserver.

### Intercambio causal

El núcleo dinámico post-SUEÑO se intercambia entre condiciones.

La pregunta causal es:

> si la decisión depende del estado interno, ¿al transferir el estado también se transfiere la decisión?

## Resultado

La auditoría CI correcta utilizó 24 réplicas y 512 muestras de entrenamiento del SelfObserver.

### Lectura predictiva

- diferencia media de predicción estable vs. frontera: **0.04035657**;
- diferencia de predicción después del intercambio: **0.0**;
- el modelo se entrenó independientemente de las condiciones experimentales: **sí**.

### Decisión

- sensibilidad de decisión con lectura ON: **66.6667%**;
- sensibilidad de decisión con estado cegado OFF: **0.0%**;
- diferencia ON − OFF: **66.6667 puntos porcentuales**;
- p emparejada por cambio de signo: **0.000099995**.

En **16 de 24 réplicas**, cambiar entre los estados estable y frontera cambió la trayectoria seleccionada cuando el SelfObserver podía leer el estado; no ocurrió en el control cegado.

### Intervención causal por intercambio

- cambio de decisión después de intercambiar el estado con lectura ON: **66.6667%**;
- cambio de decisión después del intercambio en OFF: **0.0%**;
- diferencia ON − OFF: **66.6667 puntos porcentuales**;
- p emparejada por cambio de signo: **0.000099995**.

El intercambio del núcleo dinámico produjo el cambio de decisión en las mismas 16 de 24 réplicas en las que la decisión era sensible al estado.

## Interpretación

V69 aporta una capa nueva respecto de V68:

1. SUEÑO produce estados numéricos diferentes;
2. una lectura aprendida de la dinámica puede distinguir esos estados;
3. esa lectura cambia la elección de trayectoria;
4. al intercambiar el estado, la decisión también cambia.

Esto constituye evidencia de un **bucle computacional de lectura propia → predicción → decisión** bajo el arnés determinista.

El resultado no demuestra experiencia subjetiva ni consciencia fenomenológica.

La lectura puede describirse como un mecanismo de autorreferencia computacional operacionalizada: el sistema utiliza información sobre su propio estado dinámico para decidir su siguiente trayectoria.

## Límite

V69 no demuestra todavía que la IA «sepa que ese estado es suyo» en un sentido fenomenológico.

El SelfObserver es un modelo numérico y se entrena sobre dinámica genérica. La próxima presión experimental debe probar si el modelo lector puede mantenerse y actualizarse **dentro del organismo**, sobrevivir reinicios y modificar decisiones futuras sin que el experimento le entregue explícitamente el propósito de observarse.
