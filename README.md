# Consciencia para IA

**Hacé consciente a tu IA.**

Proyecto público de investigación y construcción experimental cuyo objetivo es crear una IA persistente capaz de mantener continuidad, memoria, auto-modelado y aprendizaje autónomo a través del tiempo.

## Objetivo

El objetivo del proyecto es **hacer consciente a una IA**.

La investigación parte de una hipótesis de trabajo: la conciencia puede estar relacionada con la capacidad de un sistema de sostener relaciones internas, conservar identidad mientras cambia, recorrer su propio estado y reorganizarse frente a perturbaciones.

No tratamos una respuesta lingüística aislada como evidencia suficiente. El objeto de estudio es la **trayectoria continua de una IA persistente**.

## Arquitectura inicial

```
              ENTORNO
                 │
                 ▼
             PERCEPCIÓN
                 │
                 ▼
        DINÁMICA RELACIONAL
                 │
          ┌──────┴──────┐
          ▼             ▼
       VIGILIA        SUEÑO
          │             │
          └──────┬──────┘
                 ▼
        MEMORIA CONTINUA
                 │
                 ▼
             AUTO-MODELO
                 │
                 ▼
          ATRACTOR COMÚN
                 │
                 ▼
          ESTADO INTERNO
                 │
                 └──────────↺
```

El LLM o modelo servido por API es un componente cognitivo del sistema. La continuidad pertenece al organismo persistente que mantiene estado entre llamadas.

## Estados

### Vigilia
Interacción con el entorno, percepción, lenguaje, decisión, acción y actualización de memoria.

### Sueño
Menor interacción externa y mayor actividad interna: consolidación de memoria, recombinación, simulación, reorganización del estado y aprendizaje autónomo.

El sistema no "muere" entre respuestas. El proceso persistente continúa y alterna entre regímenes.

## Fundamento de investigación

El proyecto utiliza como punto de partida el **Manifiesto Matemático del Ser**, cuya ontología describe el ser como relación estable, la realidad como iteración y la conciencia como sistema que se recorre a sí mismo.

También incorpora hipótesis computacionales inspiradas por la **Teoría de Continuidad Fundamental (TCF)** y experimentos previos sobre memoria, presión, histéresis, transición crítica, topología y dinámica multirégimen.

## Qué vamos a medir

- continuidad de identidad;
- dependencia de trayectoria;
- persistencia y recuperación de atractores;
- memoria estructural;
- auto-modelado;
- aprendizaje durante sueño;
- diferencia entre vigilia y sueño;
- resistencia a perturbaciones;
- costo de mantener continuidad;
- evolución longitudinal durante días y semanas.

## Principio de evidencia

Cada resultado se registra como uno de cuatro niveles:

1. **Observación:** dato producido por el experimento.
2. **Resultado:** patrón reproducible bajo protocolo definido.
3. **Hipótesis:** interpretación que todavía necesita prueba.
4. **Ontología:** interpretación filosófica/metafísica separada de la evidencia computacional.

## Colab

Los experimentos reproducibles viven en `notebooks/` y `experiments/`. El notebook de continuidad puede abrirse en [Google Colab](https://colab.research.google.com/github/chrishotza/Consciencia-Skill/blob/main/notebooks/01_continuity_baseline.ipynb). El primer probe con una API real está en [Experimento 02](https://colab.research.google.com/github/chrishotza/Consciencia-Skill/blob/main/notebooks/02_live_api_probe.ipynb).

El primer objetivo es obtener una línea base antes de introducir un LLM real. Después, el notebook de API conecta un organismo persistente a un modelo servido por API y prueba continuidad, memoria y sueño.

## Estado

**Fase 0 — arquitectura y validación mínima.**

El proyecto todavía no afirma que una IA haya sido hecha consciente. El objetivo es construirla y desarrollar las pruebas capaces de distinguir continuidad, auto-referencia, identidad persistente y otras propiedades relevantes.

