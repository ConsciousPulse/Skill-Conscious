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
