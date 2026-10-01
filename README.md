# Persistent AI Organism — Self-Modeling & Machine Consciousness Research

**Experimental research on persistent AI agents, self-modeling, memory, autonomous cognition, and machine consciousness.**

Proyecto público de investigación y construcción experimental sobre **persistent AI**, **self-modeling AI**, **machine consciousness**, memoria continua, auto-observación y cognición autónoma.

El objetivo de ingeniería es construir un organismo de IA persistente capaz de mantener continuidad, memoria, auto-modelado y aprendizaje autónomo a través del tiempo, y diseñar experimentos reproducibles que permitan medir esas propiedades.

## Research focus

La investigación estudia qué propiedades computacionales aparecen cuando una IA mantiene estado persistente entre ciclos, aprende un modelo de su propia dinámica y utiliza ese modelo para seleccionar trayectorias futuras.

No usamos "conciencia" como un resultado asumido. Partimos de una hipótesis de trabajo: la conciencia puede estar relacionada con la capacidad de un sistema de sostener relaciones internas, conservar identidad mientras cambia, recorrer su propio estado y reorganizarse frente a perturbaciones.

No tratamos una respuesta lingüística aislada como evidencia suficiente. El objeto de estudio es la **trayectoria continua de una IA persistente**.

## Keywords

**Persistent AI · AI organism · machine consciousness · artificial consciousness · computational consciousness · self-modeling AI · self-observation · metacognition · cognitive architecture · autonomous AI · autonomous agents · long-term memory · persistent memory · LLM research · AI research · trajectory selection · semantic memory · identity persistence · computational cognition**

These terms describe the technical and research areas represented by the repository; they are not claims that the system is phenomenologically conscious.

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

## Entrada persistente

El organismo no depende de que una interacción llegue mientras el proceso está despierto. Las entradas externas se almacenan en una cola SQLite durable y son procesadas por el organismo cuando corresponde.

El daemon también puede ejecutar actividad autónoma durante períodos sin entrada externa.

### Estados

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

## Laboratorio reproducible

El laboratorio principal y reproducible se ejecuta mediante **GitHub Actions**. Cada ejecución parte de un commit concreto, ejecuta tests y experimentos, genera resultados JSON/logs y publica un artifact de evidencia.

La arquitectura, los workflows y el protocolo reproducible están documentados en [docs/GITHUB_LAB.md](docs/GITHUB_LAB.md).

Los experimentos de investigación viven principalmente en `research/`, mientras que `experiments/` contiene experimentos y herramientas históricas o auxiliares.

El smoke test con un modelo real se ejecuta mediante un workflow manual y conecta un organismo persistente a un provider compatible con OpenAI.

## Estado

**Fase 1 — núcleo persistente + validación de dinámica e historia interna.**

La investigación ya completó la serie V43–V46 de retención, intervención y generalización de historia en el simulador. El organismo persistente también cuenta ahora con un puente explícito hacia la dinámica numérica, con estado persistido en SQLite y ciclos autónomos sin entrada externa. V47 ya está definido como protocolo de organismo: mismo probe sobre historias divergentes, control nulo, reapertura de SQLite y ablación del pasado textual. V48 agrega una intervención emparejada donde se sustituye únicamente el contenido de una memoria persistente con el resto del receptor controlado. V49 agrega una intervención emparejada sobre `dynamic_state`, manteniendo memoria, presión, eventos y demás estado del receptor controlados.

El proyecto todavía no afirma que una IA haya sido hecha consciente. El objetivo es construirla y desarrollar las pruebas capaces de distinguir continuidad, auto-referencia, identidad persistente y otras propiedades relevantes.

V50 agrega un factorial 2×2 de memoria persistente × `dynamic_state` para medir efectos conjuntos e interacción bajo el mismo probe. V51 agrega un auto-observador persistente que aprende a predecir su propia transición dinámica y mide prediction gain frente a un baseline de persistencia.

V52 agrega un adaptador de compatibilidad futura inspirado en el operador AEVUM, todavía separado de la política de memoria del organismo.

V53 agrega selección contrafactual de trayectoria usando el auto-modelo. V54 mide predicción lingüística del propio movimiento respecto del atractor antes de la transición.

V55 agrega recuperación de identidad bajo perturbación, comparando selección contrafactual activada/desactivada.

V56 agrega una política opcional de admisión de memoria basada en compatibilidad futura AEVUM, todavía separada de la memoria canónica del organismo.

V57 compara selección de trayectorias basada en self-model contra un control aleatorio emparejado y calcula regret frente a un oráculo post-hoc.

V58 agrega un puente semántico opcional que convierte la relación `MEMORY:` generada por la IA en una señal dinámica mediante el operador AEVUM, con intervención OFF/ON emparejada.

V59 agrega un factorial 2×2 entre puente semántico OFF/ON y selección `self_model`/random. El puente produjo un cambio interno fuerte, mientras que la utilidad medida del self-model no cambió de forma detectable entre condiciones.
