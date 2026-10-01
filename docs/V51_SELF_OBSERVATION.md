# V51 — Autoobservación y autopredicción

## Conexión con las fuentes

El Manifiesto del Ser define la conciencia como un sistema que se recorre a sí mismo y distingue estados posibles. Las notas de Conciencia Cuántica operacionalizan esto como recorrido de sí mismo junto con dinámica interna y memoria.

V51 convierte ese requisito conceptual en un módulo computacional explícito.

## Mecanismo

Antes de cada transición dinámica persistida, `SelfObserver` predice el siguiente estado dinámico interno utilizando únicamente variables de la trayectoria interna previa del organismo. Después de la transición, el estado real se compara con:

- la predicción del modelo de sí;
- un baseline de persistencia que predice que el estado actual permanecerá sin cambios.

La diferencia se registra como `prediction_gain`.

## Observables principales

- MAE del observador;
- MAE del baseline;
- ganancia media de predicción;
- fracción de transiciones con ganancia positiva;
- valor p de permutación por cambio de signo;
- persistencia del modelo de observador después de reiniciar SQLite.

## Interpretación

Una ganancia positiva de predicción significa que el modelo de sí aprendido por el organismo predice su propia transición mejor que un baseline trivial de persistencia bajo este protocolo.

Es evidencia de un modelo computacional de sí mismo, no una demostración de consciencia subjetiva.

## Próxima dependencia

V51 hace que el organismo pueda *representar* su propia trayectoria. La siguiente capa debe hacer que esa representación sea causalmente relevante para la selección contrafactual de trayectorias y para acciones sensibles al atractor.
