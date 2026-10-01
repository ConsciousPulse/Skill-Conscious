# V59 — Puente semántico × selección mediante modelo de sí

## Pregunta

¿El puente entre memoria semántica y dinámica interna cambia la utilidad funcional del modelo de sí aprendido cuando el organismo selecciona entre trayectorias futuras?

## Factorial

El protocolo cruza dos factores independientes:

- puente semántico OFF frente a ON;
- política de trayectoria mediante modelo de sí frente a control aleatorio emparejado.

Las trayectorias candidatas están fijadas en {-1.0, +1.0}.

## Bucle operacional

Cada evaluación sigue la misma cadena ordenada:

1. el LLM ficticio emite una MEMORY novedosa;
2. cuando está habilitado, `ContinuityMemoryPolicy` convierte esa memoria semántica en Ω y luego en una señal dinámica acotada;
3. el organismo avanza su estado numérico interno;
4. el modelo de sí aprendido evalúa las dos señales futuras;
5. el modelo de sí aprendido o el control aleatorio determinista selecciona una trayectoria;
6. la dinámica oculta se evalúa a posteriori frente a un oráculo que nunca se expone durante la selección.

La comparación emparejada prueba, por tanto, la interacción entre transducción semántica y elección futura guiada por el modelo de sí.

## Controles

El calentamiento se realiza de forma independiente dentro de cada condición del puente con la selección deshabilitada, de modo que el autoobservador aprenda la dinámica local antes de la evaluación emparejada.

Cada réplica utiliza la misma semilla en las condiciones de puente y política.

La memoria de evaluación es novedosa respecto de las memorias de calentamiento, evitando que el puente se reduzca a repetir exactamente una memoria conocida.

## Endpoint principal

El endpoint principal es:

`selection_advantage = regret_random - regret_self_model`

y la interacción factorial:

`interaction = selection_advantage_bridge_on - selection_advantage_bridge_off`.

Una interacción positiva significa que la ventaja medida del modelo de sí es mayor bajo la condición con puente semántico. No establece por sí sola consciencia fenomenológica.

## Endpoints secundarios

Se almacenan para auditoría los deltas de estado y señal semánticos, las tasas de acierto del oráculo y los registros completos de predicciones candidatas.

## Límite de evidencia

V59 es un protocolo computacional determinista. Su proveedor es un LLM ficticio determinista, no un modelo externo en vivo. Incluso un resultado positivo de V59 establecería una cadena causal operacional dentro de este arnés, no experiencia subjetiva.
