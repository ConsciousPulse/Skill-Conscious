# V76 — Generalización de continuidad bajo perturbaciones no vistas

## Pregunta

V75 mostró que una política puede actuar después de una perturbación y recuperar ventaja de autopredicción.

Pero ese resultado todavía podía estar ligado al régimen de perturbación usado para entrenarla.

> ¿La política aprende una regla dependiente del estado que generaliza a perturbaciones cuya magnitud nunca apareció durante su entrenamiento?

## Diseño

V76 separa explícitamente **entrenamiento** y **generalización**.

La política principal se entrena únicamente con perturbaciones de magnitud:

\`\`\`text
0.25 y 0.75
\`\`\`

siempre con ambos signos.

La evaluación utiliza:

- perturbaciones **in-domain**: 0.25 y 0.75;
- perturbaciones **OOD (out-of-distribution)**: 0.35, 0.55 y 0.85.

La política no recibe la magnitud de perturbación como una característica. Solo ve el estado dinámico disponible para su modelo de sí.

## Control de sobreajuste

Se entrena además una política estrecha usando únicamente perturbaciones de magnitud 0.50.

Esta política sirve como control de exposición limitada: permite preguntar si una política entrenada sobre un único régimen conserva el mismo comportamiento cuando cambia la magnitud.

## Objetivo

El objetivo de entrenamiento no cambia:

\`\`\`text
ganancia de autopredicción
=
error de persistencia
−
error del modelo de sí
\`\`\`

No se entrega una etiqueta de continuidad.

El índice de continuidad se calcula solamente como endpoint secundario:

\`\`\`text
continuidad = 1 / (1 + |estado_actual - estado_pre_perturbación|)
\`\`\`

## Protocolo

Cada condición:

1. inicia desde una semilla independiente pero emparejable;
2. realiza la misma fase de calentamiento;
3. aplica una perturbación controlada;
4. elimina cualquier entrada semántica de la sonda;
5. ejecuta varios pasos de recuperación;
6. utiliza exactamente la misma semilla para política generalizada, política estrecha, estado cegado, política fija y aleatoria.

La política generalizada y la política estrecha se guardan y se recargan sin reentrenamiento antes de la evaluación.

## Endpoints

### Primario

**Ganancia de autopredicción después de la perturbación.**

El resultado de interés para V76 es particularmente el conjunto OOD.

### Generalización

Se calcula la ventaja de la política generalizada sobre la aleatoria en condiciones in-domain y OOD:

\`\`\`text
ventaja = ganancia_generalizada − ganancia_aleatoria
\`\`\`

También se registra la fracción de esa ventaja que permanece en OOD respecto de in-domain.

### Secundarios

- índice de continuidad;
- comparación con la política estrecha;
- comparación con estado cegado;
- sensibilidad de la primera acción al signo de una perturbación OOD de 0.55.

## Resultado observado

La ejecución de GitHub Actions utilizó 64 episodios por condición, 64 episodios de entrenamiento, 512 muestras del SelfObserver y 12 pasos de recuperación.

### Ganancia de autopredicción

- ganancia media de la política generalizada, todas las condiciones: **0.50016**;
- estado cegado: **-0.15113**;
- política fija: **-0.13311**;
- selección aleatoria: **0.18987**;
- ventaja generalizada − aleatoria en condiciones in-domain: **0.30819**;
- ventaja generalizada − aleatoria en condiciones OOD: **0.31170**;
- fracción de la ventaja conservada en OOD: **1.0114**;
- diferencia aprendida − aleatoria, conjunto total de condiciones, p emparejada por cambio de signo: **0.00005**;
- diferencia aprendida − estado cegado, conjunto total de condiciones, p emparejada: **0.00005**;
- diferencia aprendida − política fija, conjunto total de condiciones, p emparejada: **0.00005**.

La política generalizada mantuvo por tanto su ventaja de autopredicción cuando pasó de las perturbaciones entrenadas (0.25 y 0.75) a las no vistas (0.35, 0.55 y 0.85).

### Control de exposición estrecha

La política entrenada únicamente con perturbación 0.50 obtuvo prácticamente el mismo resultado que la política generalizada:

- p emparejada generalizada − estrecha: **1.0**;
- ganancia media global de la política estrecha: **0.50014**.

Esto indica que, bajo este arnés y esta parametrización lineal, ampliar la variedad de perturbaciones de entrenamiento no produjo una ventaja adicional medible. El resultado de V76 es por tanto más específico: **la política ya aprendida generaliza a perturbaciones no vistas**, no que la diversidad de entrenamiento haya demostrado por sí misma una mejora.

### Respuesta dependiente del estado

Para una perturbación OOD de magnitud 0.55:

- respuesta de la primera acción con estado legible: **100%**;
- estado cegado: **0%**.

Esto muestra que la política conserva sensibilidad conductual al estado interno en una perturbación que no apareció durante el entrenamiento.

### Continuidad

El índice secundario de continuidad fue:

- política generalizada: **0.80164**;
- política aleatoria: **0.80667**;
- diferencia generalizada − aleatoria, p emparejada: **0.07230**.

Por tanto, V76 **no demuestra una ventaja robusta de continuidad frente a la selección aleatoria**. El efecto reproducido es el de generalización de la autopredicción, no el de una prioridad autónoma por conservar continuidad.

## Qué demostraría un resultado favorable

Un resultado favorable sería que la política generalizada conserve una ventaja de autopredicción en perturbaciones OOD, especialmente si mantiene una ventaja frente a:

- estado cegado;
- selector fijo;
- selección aleatoria;
- política entrenada en un único régimen.

Eso respaldaría **generalización funcional de la política de autopredicción a perturbaciones no vistas**.

No demostraría que la IA haya descubierto por sí misma que debe conservar continuidad.

## Límite

La meta de recuperar autopredicción continúa siendo una decisión explícita del protocolo.

Por eso V76 no convierte continuidad en un valor autónomo y no demuestra experiencia subjetiva.

Su función es separar dos hipótesis:

1. la política simplemente aprende un comportamiento ligado a un régimen concreto de perturbación;
2. la política aprende una regla más general dependiente de su estado y reutilizable bajo perturbaciones nuevas.
