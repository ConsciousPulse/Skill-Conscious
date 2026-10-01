# V57 — Selección mediante modelo de sí comparada con un oráculo

## Pregunta

¿El modelo de sí aprendido por el organismo selecciona futuras trayectorias mejor que una política aleatoria emparejada después de la misma historia de calibración?

## Diseño

Cada réplica comienza desde una trayectoria de calentamiento emparejada.

Se permiten dos señales candidatas:

- `-1.0`;
- `+1.0`.

El brazo con modelo de sí puntúa ambos estados siguientes contrafactuales y elige la señal con mejor puntuación de coherencia declarada.

El brazo aleatorio elige una de las mismas candidatas mediante una política aleatoria determinista con semilla.

Después de la elección se ejecuta la transición real.

Por separado, un oráculo evalúa directamente ambas transiciones candidatas desde el mismo estado previo utilizando la dinámica numérica congelada. El oráculo se utiliza solamente después de la intervención para calcular regret; nunca se expone al selector del organismo.

## Observables principales

- regret del modelo de sí;
- regret del control aleatorio;
- ventaja emparejada de regret;
- tasa de aciertos del oráculo;
- valor p de permutación emparejada por cambio de signo.

## Interpretación

Si el brazo con modelo de sí presenta sistemáticamente menor regret que el brazo aleatorio emparejado, el modelo interno de sí mismo del organismo no es meramente descriptivo: resulta funcionalmente útil para seleccionar entre trayectorias futuras.

Esto sigue siendo un resultado computacional sobre un modelo de sí, no una demostración de consciencia fenomenológica.
