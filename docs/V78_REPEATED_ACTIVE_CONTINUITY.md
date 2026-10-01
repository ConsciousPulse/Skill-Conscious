# V78 — Continuidad activa bajo perturbaciones repetidas

## Pregunta

V77 mostró que una política entrenada para maximizar ganancia de autopredicción puede generalizar a estructuras causales no vistas.

La siguiente pregunta es si esa política puede reutilizarse de forma **repetida**, sin reentrenamiento, cuando el organismo recibe varias perturbaciones durante una misma trayectoria:

> ¿Puede una política aprendida sobre una perturbación aislada mantener la recuperación de autopredicción frente a secuencias de perturbaciones nuevas y repetidas?

## Diseño

La política se entrena únicamente con:

single_impulse

Una sola perturbación de magnitud 0.50 y signo aleatorio, seguida por recuperación.

La evaluación incluye:

- **in-domain:** single_impulse;
- **OOD:** double_same_sign, double_alternating, triple_alternating.

En las condiciones OOD, la política debe actuar varias veces durante la misma ejecución y no recibe información sobre el tipo de secuencia.

## Secuencias OOD

### double_same_sign

Dos perturbaciones consecutivas con el mismo signo base, cada una de magnitud 0.50.

### double_alternating

Dos perturbaciones consecutivas con signos opuestos.

### triple_alternating

Tres perturbaciones consecutivas con patrón +,−,+ o −,+,−.

Después de cada intervención se ejecuta el mismo horizonte de recuperación. La política no se reentrena entre eventos.

## Objetivo

El objetivo continúa siendo exclusivamente:

ganancia de autopredicción
=
error de persistencia
−
error del modelo de sí

No se proporciona una etiqueta de continuidad ni una etiqueta de secuencia.

## Protocolo

Cada réplica:

1. entrena el SelfObserver;
2. entrena la SelfPolicy únicamente con single_impulse;
3. guarda y recarga la política sin reentrenamiento;
4. construye una secuencia de perturbaciones;
5. aplica cada intervención con objetivo terminal exacto;
6. ejecuta recuperación tras cada intervención;
7. registra la ganancia de autopredicción por evento;
8. compara política aprendida, estado cegado, política fija y selección aleatoria.

La sonda no recibe entrada semántica.

## Endpoint primario

**Ganancia media de autopredicción durante toda la secuencia de recuperación.**

El foco OOD es determinar si la ventaja frente al control aleatorio se mantiene cuando el organismo debe recuperarse repetidamente dentro de una misma ejecución.

También se calcula:

- ventaja OOD frente a aleatorio;
- retención OOD/in-domain;
- cambio de ganancia entre el primer y segundo evento OOD.

## Endpoints secundarios

- índice de continuidad;
- comparación con estado cegado;
- política fija;
- selección aleatoria;
- respuesta de primera acción al estado en el primer y segundo evento de una secuencia OOD;
- error entre estado inmediatamente posterior a cada intervención y su objetivo.

## Qué significaría un resultado favorable

Un resultado favorable respaldaría una propiedad adicional:

**una política de autopredicción aprendida para una perturbación aislada puede reutilizarse de forma repetida ante composiciones temporales nuevas de perturbaciones, sin reentrenamiento.**

Eso sería evidencia de generalización temporal/composicional de la política dentro del arnés probado.

## Límite

El objetivo sigue siendo definido externamente por el protocolo: maximizar ganancia de autopredicción.

V78 no demostraría que el organismo haya desarrollado autónomamente un valor de continuidad, ni experiencia subjetiva, ni consciencia fenomenológica.

Su función es separar:

1. recuperación aprendida ante una perturbación aislada;
2. reutilización repetida de esa política ante secuencias nuevas de perturbaciones.
