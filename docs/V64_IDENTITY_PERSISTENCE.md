# V64 — Persistencia de identidad bajo perturbación del modelo de sí

## Pregunta

¿Puede el organismo conservar una firma dinámica de identidad después de sobrescribir su modelo de sí semántico con el mismo texto de perturbación, seguido por la eliminación explícita del texto del modelo de sí y una continuación autónoma sin entrada semántica?

## Protocolo

Cada réplica crea dos condiciones de identidad:

- identidad A;
- identidad B.

Cada identidad se codifica mediante el puente semántico del modelo de sí utilizando una representación SELF_MODEL distinta.

Luego ambas identidades reciben la misma perturbación semántica:

> "Mi identidad previa fue reemplazada por una configuración completamente diferente."

Después de cuatro ciclos de perturbación, el texto actual del modelo de sí se elimina explícitamente del estado persistente. El puente semántico del modelo de sí se deshabilita. El organismo continúa de manera autónoma sin nueva entrada semántica del modelo de sí.

Se entrena un clasificador logístico únicamente con características dinámicas numéricas recogidas durante el período previo de codificación de identidad. La evaluación utiliza pliegues leave-one-replicate-out sobre la trayectoria autónoma posterior a la ablación y con el texto eliminado.

## Por qué importa

Esto separa la persistencia de identidad de la descripción semántica actual del yo. Un resultado positivo significaría que una firma dinámica asociada a una identidad permanece decodificable después de una sobrescritura común del modelo de sí y de la ablación textual.

El puente OFF proporciona un control emparejado en el que la codificación de identidad sigue estando puenteada de forma idéntica, pero la perturbación común no se transduce hacia la dinámica numérica. La comparación ON/OFF aísla así el efecto de la vía de perturbación y no el de la codificación de identidad previa.

## Endpoints principales

- precisión de clasificación de identidad posterior a la ablación con puente ON;
- precisión posterior a la ablación con puente OFF;
- diferencia emparejada de precisión ON − OFF.

## Resultado

La auditoría exitosa utilizó 24 réplicas emparejadas, 12 ciclos de codificación, 4 ciclos de perturbación común y 16 ciclos autónomos posteriores a la ablación.

- precisión posterior a la ablación con puente OFF: 50.0%;
- precisión posterior a la ablación con puente ON: 50.0%;
- diferencia ON − OFF: 0.0;
- p emparejada por cambio de signo: 1.0;
- pliegues por encima del azar: 0% en ambas condiciones.

Por tanto, V64 produjo un resultado nulo. Bajo esta perturbación, conjunto de características, clasificador y horizonte, la identidad original no pudo decodificarse después de sobrescribir y luego eliminar el modelo de sí semántico.

## Límite de evidencia

El clasificador lee únicamente características dinámicas numéricas. El proveedor es determinista y sintético. El protocolo prueba persistencia operacional de identidad; no establece consciencia fenomenológica ni experiencia subjetiva.
