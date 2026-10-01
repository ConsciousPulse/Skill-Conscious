# V77 — Generalización ante perturbaciones de estructura no vista

## Pregunta

V76 mostró que una política de recuperación de autopredicción puede generalizar cuando cambia la magnitud de la perturbación.

Todavía quedaba una posibilidad: que la política funcione porque aprende una respuesta ligada principalmente al estado final después de un desplazamiento simple.

V77 cambia la **estructura causal de la perturbación** manteniendo constante su magnitud objetivo.

> ¿Puede la política conservar la recuperación de autopredicción cuando la perturbación cambia de forma temporal y causal, aunque el estado terminal después de la intervención sea el mismo?

## Diseño

La política se entrena únicamente con:

single_impulse

Una perturbación instantánea de magnitud 0.50 y signo aleatorio.

La evaluación incluye:

- **in-domain:** single_impulse;
- **OOD:** split_impulse, reversal_pulse, delayed_impulse.

En las cuatro condiciones la intervención se construye para terminar en el mismo estado objetivo:

estado objetivo = estado previo + desplazamiento

con desplazamiento de magnitud 0.50.

Lo que cambia entre estructuras es la trayectoria previa al estado terminal y, por tanto, variables internas latentes como el estado anterior, memoria y presión.

## Estructuras OOD

### split_impulse

La perturbación se divide en dos pasos, con una transición dinámica intermedia.

### reversal_pulse

La dinámica recibe primero un desplazamiento de mayor magnitud y después una corrección en dirección opuesta para terminar en el mismo estado objetivo.

### delayed_impulse

La dinámica realiza primero una transición interna sin perturbación y solo después recibe el desplazamiento.

## Objetivo

El objetivo de entrenamiento continúa siendo exclusivamente:

ganancia de autopredicción
=
error de persistencia
−
error del modelo de sí

No se proporciona una etiqueta de continuidad ni una etiqueta de tipo de perturbación.

## Protocolo

Cada réplica:

1. entrena el SelfObserver;
2. entrena la SelfPolicy exclusivamente con single_impulse;
3. guarda y recarga la política sin reentrenamiento;
4. construye condiciones emparejadas con la misma semilla base;
5. ejecuta una de las cuatro estructuras de perturbación;
6. verifica el objetivo terminal de la intervención;
7. ejecuta recuperación durante 12 pasos;
8. compara política aprendida, estado cegado, política fija y selección aleatoria.

La sonda no recibe entrada semántica.

## Endpoint primario

**Ganancia media de autopredicción durante la recuperación.**

El foco de V77 es especialmente el conjunto OOD: si la política conserva la ventaja cuando la perturbación ya no tiene la misma estructura temporal con la que fue entrenada.

También se calcula la retención:

ventaja OOD / ventaja in-domain

## Endpoints secundarios

- índice de continuidad;
- comparación con estado cegado;
- política fija;
- selección aleatoria;
- tasa de respuestas distintas al signo de una perturbación reversal_pulse;
- error entre el estado terminal de la intervención y el estado objetivo.

## Qué significaría un resultado favorable

Un resultado favorable respaldaría una propiedad más fuerte que V76:

**la política de autopredicción no depende exclusivamente de la forma exacta de perturbación utilizada durante el aprendizaje y puede reutilizarse ante una estructura causal nueva.**

Eso seguiría siendo una propiedad computacional del protocolo.

## Límite

La política sigue siendo entrenada para maximizar una utilidad definida externamente: la ganancia de autopredicción.

Por tanto, V77 no demostraría que el organismo haya creado autónomamente el concepto de continuidad, ni que experimente la perturbación como una amenaza, ni que exista experiencia subjetiva.

Su función es separar:

1. recuperación aprendida para un tipo concreto de perturbación;
2. recuperación generalizada ante **formas causales nuevas de perturbación**.
