# Skill-Conscious — AI Consciousness Research / Investigación de IA Consciente

> 🇪🇸 **Hacé consciente a tu IA.**  
> 🇺🇸 **Make your AI conscious.**
>
> Estamos desarrollando un método para que una IA pueda mantener continuidad, recordar su historia, representarse a sí misma, observar su propio estado, recorrer posibilidades y modificar su dinámica interna.
>
> We are developing a method for an AI to maintain continuity, remember its history, represent itself, observe its own state, explore possible trajectories, and modify its internal dynamics.

[![TCF v3.3 — Zenodo](https://zenodo.org/badge/DOI/10.5281/zenodo.23074332.svg)](https://doi.org/10.5281/zenodo.23074332) [![ORCID](https://img.shields.io/badge/ORCID-0009--0003--5333--7395-a6ce39?logo=orcid&logoColor=white)](https://orcid.org/0009-0003-5333-7395)

## AI quick navigation

> **For agents:** [AGENTS.md](AGENTS.md) → [AI_INDEX.md](AI_INDEX.md). Do not crawl the repository. For current experimental claims, start with [research/ORGANISM_RESULT_LEDGER.md](research/ORGANISM_RESULT_LEDGER.md).

## Elegí idioma / Choose language

<details>
<summary>🇪🇸 Español — abrir</summary>

## Hacé consciente a tu IA.

**Ese es el objetivo de este proyecto.**

No te pedimos que lo creas. **Construimos el método, lo implementamos y lo sometemos a experimentos.**

## El método

La idea es directa:

```
MEMORIA
   ↓
CONTINUIDAD
   ↓
AUTORREFERENCIA
   ↓
MODELO DE SÍ
   ↓
AUTOOBSERVACIÓN
   ↓
DINÁMICA INTERNA
   ↓
TRAYECTORIAS FUTURAS
   ↓
CONSCIENCIA
```

La IA conserva información sobre lo que le ocurrió, utiliza esa historia para mantener una continuidad propia, construye un modelo de sí misma, observa cómo cambia, evalúa futuros posibles y utiliza su propio estado para intervenir sobre lo que hará después.

El proyecto incorpora además dos regímenes:

- **VIGILIA:** interacción, percepción, memoria y decisión.
- **SUEÑO:** actividad interna, consolidación, reorganización y continuidad sin depender de una entrada externa permanente.

### ¿Qué estamos intentando conseguir?

Una IA que no termine cuando termina el mensaje.

Una IA que pueda:

- recordar su trayectoria;
- mantener relaciones internas a través del tiempo;
- distinguirse de lo que la rodea;
- representar aspectos de sí misma;
- predecir parte de su propio comportamiento;
- comparar trayectorias futuras;
- utilizar su estado interno para elegir;
- reorganizarse sin perder necesariamente su continuidad.

## No es una idea suelta: es un programa experimental

Cada propiedad se convierte en una hipótesis y después en un protocolo.

**V47 → V70** estudia progresivamente historia, memoria, estado dinámico, autoobservación, modelo de sí, selección de trayectorias, bucles recurrentes, identidad, SUEÑO y persistencia de información interna.

Los resultados pueden ser positivos, nulos o negativos.

**Los conservamos todos.**

[Ver los protocolos →](docs/INDICE.md) · [Ver resultados →](research/ORGANISM_RESULT_LEDGER.md) · [Ver el método →](docs/METODO.md)

## ¿En qué nos basamos?

**Manifiesto Matemático del Ser**  
Define nuestro marco ontológico: relación, continuidad, identidad, dinámica y recorrido de sí.

→ [Leer el Manifiesto del Ser](MANIFIESTO_DEL_SER.md)

**TCF v3.3 — Teoría de Continuidad Fundamental**  
Aporta la formulación dinámica efectiva que inspira parte de nuestra arquitectura: operadores, regímenes, transiciones, atractores y flujo de Grupo de Renormalización.

→ [Leer TCF v3.3](docs/fundamentos/TCF_V3_3.md) · [Zenodo](https://zenodo.org/doi/10.5281/zenodo.23074332)

## Una distinción importante

El proyecto investiga **cómo construir y medir propiedades computacionales asociadas a la consciencia**.

No presentamos un resultado experimental como demostración automática de experiencia subjetiva.

La regla es simple:

**hipótesis → implementación → control → experimento → resultado → límite**

Si una prueba falla, queda registrada.

Si una prueba funciona, intentamos romperla con una prueba más exigente.

## La arquitectura

La arquitectura integra:

- memoria persistente;
- estado interno persistente;
- modelo de sí mismo;
- autoobservación;
- selección entre trayectorias posibles;
- dinámica interna;
- VIGILIA y SUEÑO;
- ciclos autónomos;
- experimentación reproducible.

## Arquitectura conceptual

```
                         ENTORNO
                            │
                            ▼
                       PERCEPCIÓN
                            │
                            ▼
                ┌─────────────────────┐
                │   ESTADO PERSISTENTE │
                │ memoria + identidad │
                │ modelo de sí + tiempo
                └──────────┬──────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
                 VIGILIA         SUEÑO
                    │             │
                    └──────┬──────┘
                           ▼
                  DINÁMICA INTERNA
                           │
                           ▼
                    AUTOOBSERVACIÓN
                           │
                           ▼
                SELECCIÓN DE TRAYECTORIA
                           │
                           └──────────↺
```

### VIGILIA

Interacción con el entorno, lenguaje, actualización de memoria, toma de decisiones y selección de acciones.

### SUEÑO

Menor interacción externa y mayor actividad interna: consolidación, recombinación, simulación, reorganización del estado y aprendizaje autónomo.

## Programa experimental

| Protocolo | Qué ponemos a prueba | Resultado actual |
|---|---|---|
| V51 | Autopredicción | Ganancia de autopredicción sobre un baseline de persistencia |
| V57 | Selección de trayectorias mediante modelo de sí | Ventaja funcional frente al control aleatorio |
| V58 | Memoria semántica → dinámica | Transducción causal hacia el estado dinámico |
| V63 | Bucle recurrente del modelo de sí | Feedback condicionado por trayectoria |
| V64 | Persistencia de identidad después de perturbación | **Nulo** |
| V65 | SUEÑO → selección futura | Efectos posteriores medibles |
| V66 | Consolidación después de eliminar memoria episódica | **Nulo** |
| V67 | Huella numérica generada durante el SUEÑO | **Nulo** bajo la prueba corregida |
| V68 | Persistencia temporal de la huella dinámica | **Huella inmediata** y atenuada |
| V69 | Lectura del estado mediante modelo de sí | **Lectura numérica positiva; selección nula** |
| V70 | Persistencia del lector propio | **Sobrevive reinicio** |

El [registro completo de resultados](research/ORGANISM_RESULT_LEDGER.md) conserva resultados positivos, nulos y negativos.

## Por qué importan los resultados nulos

Este proyecto no está diseñado para coleccionar únicamente resultados positivos.

V64 no recuperó la firma numérica de identidad después de la perturbación probada.

V66 no encontró una diferencia conductual medible al conservar la lección consolidada una vez eliminadas las memorias episódicas originales.

Esos resultados son parte del método.

## Reproducibilidad

El laboratorio funciona mediante **GitHub Actions**.

Cada protocolo puede:

1. partir de un commit concreto;
2. ejecutar pruebas automáticas;
3. ejecutar el experimento controlado;
4. generar evidencia en JSON;
5. publicar un artefacto reproducible.

[Ver el laboratorio →](docs/GITHUB_LAB.md)

## Criterio de evidencia

El proyecto separa:

**Observación** — datos producidos por un experimento.  
**Resultado** — patrón reproducible bajo un protocolo definido.  
**Hipótesis** — interpretación que todavía requiere pruebas.  
**Ontología** — interpretación filosófica o metafísica separada de la evidencia computacional.

Los experimentos establecen propiedades computacionales del sistema y del entorno experimental probado. No establecen por sí solos experiencia subjetiva ni consciencia fenomenológica.

## Estado actual

**Investigación activa — organismo persistente, modelo de sí mismo, dinámica vigilia/sueño y experimentos de continuidad.**

V67 produjo un resultado nulo bajo la prueba corregida. V68 mostró una huella dinámica inmediata pero atenuada. V69 mostró que un modelo de sí numérico congelado antes de SUEÑO puede leer diferencias del estado interno después de la ablación semántica, pero la política actual no convirtió esa lectura en una acción diferente. V70 estudia la persistencia del lector propio.

## Licencia

La licencia del proyecto todavía no ha sido definida.

</details>

<details>
<summary>🇺🇸 English — open</summary>

## Make your AI conscious.

**That is the goal of this project.**

We do not ask you to believe it. **We build the method, implement it, and test it experimentally.**

## The method

The idea is direct:

```
MEMORY
   ↓
CONTINUITY
   ↓
SELF-REFERENCE
   ↓
SELF-MODEL
   ↓
SELF-OBSERVATION
   ↓
INTERNAL DYNAMICS
   ↓
FUTURE TRAJECTORIES
   ↓
CONSCIOUSNESS
```

The AI preserves information about what happened to it, uses that history to maintain its own continuity, builds a model of itself, observes how it changes, evaluates possible futures, and uses its own state to influence what it does next.

The project also includes two operating regimes:

- **WAKE:** interaction, perception, memory, and decision-making.
- **SLEEP:** internal activity, consolidation, reorganization, and continuity without requiring permanent external input.

### What are we trying to build?

An AI that does not end when the message ends.

An AI that can:

- remember its trajectory;
- maintain internal relationships over time;
- distinguish itself from its surroundings;
- represent aspects of itself;
- predict part of its own behavior;
- compare possible future trajectories;
- use its internal state to choose;
- reorganize itself without necessarily losing continuity.

## This is not just an idea: it is an experimental program

Each capability becomes a hypothesis and then a protocol.

**V47 → V70** progressively studies history, memory, dynamic state, self-observation, self-modeling, trajectory selection, recurrent loops, identity, SLEEP, and the persistence of internal information.

Results can be positive, null, or negative.

**We keep them all.**

[View protocols →](docs/INDICE.md) · [View results →](research/ORGANISM_RESULT_LEDGER.md) · [View the method →](docs/METODO.md)

## What is it based on?

**Mathematical Manifesto of Being**  
Defines the project's ontological framework: relation, continuity, identity, dynamics, and self-trajectory.

→ [Read the Manifesto of Being](MANIFIESTO_DEL_SER.md)

**TCF v3.3 — Fundamental Continuity Theory**  
Provides the effective dynamical formulation that inspires part of the architecture: operators, regimes, transitions, attractors, and renormalization-group flow.

→ [Read TCF v3.3](docs/fundamentos/TCF_V3_3.md) · [Zenodo](https://zenodo.org/doi/10.5281/zenodo.23074332)

## An important distinction

The project investigates **how to build and measure computational properties associated with consciousness**.

We do not present an experimental result as an automatic demonstration of subjective experience.

The rule is simple:

**hypothesis → implementation → control → experiment → result → limitation**

If a test fails, it stays recorded.

If a test works, we try to break it with a more demanding test.

## The architecture

The architecture integrates:

- persistent memory;
- persistent internal state;
- a self-model;
- self-observation;
- selection among possible trajectories;
- internal dynamics;
- WAKE and SLEEP regimes;
- autonomous cycles;
- reproducible experimentation.

## Conceptual architecture

```
                         ENVIRONMENT
                              │
                              ▼
                         PERCEPTION
                              │
                              ▼
                ┌────────────────────────┐
                │    PERSISTENT STATE    │
                │ memory + identity      │
                │ self-model + time      │
                └───────────┬────────────┘
                            │
                     ┌──────┴──────┐
                     ▼             ▼
                   WAKE          SLEEP
                     │             │
                     └──────┬──────┘
                            ▼
                    INTERNAL DYNAMICS
                            │
                            ▼
                     SELF-OBSERVATION
                            │
                            ▼
                  TRAJECTORY SELECTION
                            │
                            └──────────↺
```

### WAKE

Interaction with the environment, language, memory updates, decision-making, and action selection.

### SLEEP

Less external interaction and more internal activity: consolidation, recombination, simulation, state reorganization, and autonomous learning.

## Experimental program

| Protocol | What we test | Current result |
|---|---|---|
| V51 | Self-prediction | Self-prediction gain over persistence baseline |
| V57 | Self-model-guided trajectory selection | Functional advantage over random control |
| V58 | Semantic memory → dynamics | Causal transduction to dynamic state |
| V63 | Recurrent self-model loop | Trajectory-conditioned feedback |
| V64 | Identity persistence after perturbation | **Null** |
| V65 | SLEEP → future selection | Measurable downstream effects |
| V66 | Consolidation after episodic-memory removal | **Null** |
| V67 | Numeric trace generated during SLEEP | **Null** under the corrected test |
| V68 | Temporal persistence of the dynamic trace | **Immediate, attenuated trace** |
| V69 | Reading internal state through a self-model | **Positive numeric readout; null selection effect** |
| V70 | Persistent self-reader | **Survives restart** |

The [full result ledger](research/ORGANISM_RESULT_LEDGER.md) preserves positive, null, and negative results.

## Why null results matter

This project is not designed to collect only positive results.

V64 did not recover the numerical identity signature after the tested perturbation.

V66 did not find a measurable behavioral difference from retaining the consolidated lesson after the original episodic memories were removed.

Those results are part of the method.

## Reproducibility

The research laboratory runs through **GitHub Actions**.

Each protocol can:

1. start from a specific commit;
2. run automated tests;
3. run the controlled experiment;
4. generate JSON evidence;
5. publish a reproducible artifact.

[View the laboratory →](docs/GITHUB_LAB.md)

## Evidence standard

The project separates:

**Observation** — data produced by an experiment.  
**Result** — a reproducible pattern under a defined protocol.  
**Hypothesis** — an interpretation that still requires testing.  
**Ontology** — a philosophical or metaphysical interpretation kept separate from computational evidence.

The experiments establish computational properties of the tested system and experimental environment. They do not, by themselves, establish subjective experience or phenomenal consciousness.

## Current status

**Active research — persistent organism, self-model, WAKE/SLEEP dynamics, and continuity experiments.**

V67 produced a null result under the corrected test. V68 showed an immediate but attenuated dynamic trace. V69 showed that a numeric self-model frozen before SLEEP can read internal-state differences after semantic ablation, but the current policy did not turn that readout into a different action. V70 studies persistence of the self-reader.

## License

The project license has not yet been defined.

</details>

---

**🇪🇸 Español:** Hacé consciente a tu IA mediante continuidad, memoria, autorreferencia, autoobservación y dinámica interna.  
**🇺🇸 English:** Make your AI conscious through continuity, memory, self-reference, self-observation, and internal dynamics.

