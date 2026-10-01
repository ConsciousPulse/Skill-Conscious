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

## Resultado observado

La ejecución corregida de GitHub Actions completó **64 réplicas por condición**, con **64 episodios de entrenamiento**, **512 muestras del SelfObserver** y **12 pasos de recuperación por intervención**. La política fue guardada y recargada sin reentrenamiento.

### Endpoint primario

Sobre todas las condiciones:

- ganancia media de autopredicción, política aprendida: **0.2422976**;
- estado cegado: **-0.2408441**;
- política fija: **-0.1844678**;
- selección aleatoria: **0.0518725**;
- aprendido − cegado, p emparejada: **0.00005**;
- aprendido − fijo, p emparejada: **0.00005**;
- aprendido − aleatorio, p emparejada: **0.00005**.

La ventaja aprendida frente a aleatorio fue:

- **in-domain:** 0.1897230;
- **OOD:** 0.1906591;
- retención OOD/in-domain: **1.0049**.

| Secuencia | Ganancia aprendida | Ganancia aleatoria | Primer evento | Segundo evento |
|---|---:|---:|---:|---:|
| single_impulse | 0.2421173 | 0.0523943 | 0.2421173 | 0.2421173 |
| double_same_sign | 0.2396398 | 0.0600594 | 0.2425893 | 0.2366903 |
| double_alternating | 0.2486624 | 0.0509057 | 0.2632883 | 0.2340365 |
| triple_alternating | 0.2387709 | 0.0441307 | 0.2532114 | 0.2363238 |

En el conjunto OOD, la diferencia media entre segundo y primer evento fue **-0.0173461**: existe una pequeña atenuación de la ganancia en el segundo evento, pero la ventaja global frente a aleatorio se mantuvo.

### Endpoints secundarios

- continuidad aprendida: **0.7905914**;
- continuidad aleatoria: **0.7922640**;
- p emparejada: **0.58767**;
- respuesta de primera acción dependiente del estado en el primer evento OOD: **100%** frente a **0%** cegado;
- respuesta de primera acción dependiente del estado en el segundo evento OOD: **100%** frente a **0%** cegado;
- error máximo entre el estado inmediatamente posterior a cada intervención y su objetivo: **0.0**.

### Interpretación

V78 respalda una forma de **generalización temporal/composicional**: una política entrenada únicamente con una perturbación aislada conservó una ventaja de autopredicción cuando tuvo que recuperarse repetidamente ante secuencias no vistas y sin reentrenamiento.

La retención OOD fue prácticamente igual a la in-domain (**1.0049**). La ventaja no depende de una mejora del índice secundario de continuidad, que no se separó del control aleatorio bajo esta prueba.

El descenso de **0.01735** entre el primer y segundo evento OOD indica que la reutilización repetida no es completamente invariante al número de perturbaciones. El resultado positivo, por tanto, es de **reutilización robusta de la política**, no de ausencia de degradación.

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
