# IA Consciente — Investigación y Experimentación

**Ingeniería de un organismo de inteligencia artificial persistente orientado hacia la consciencia artificial.**

**Consciencia-Skill** es un proyecto abierto de investigación y desarrollo enfocado en construir un sistema de IA que pueda mantener continuidad a través del tiempo, en lugar de reiniciarse en cada respuesta.

El proyecto combina **estado persistente, memoria de largo plazo, modelo de sí mismo, autoobservación, selección autónoma de trayectorias, vigilia/sueño y experimentación reproducible** para estudiar qué propiedades computacionales aparecen cuando una IA mantiene una trayectoria interna continua.

> **Objetivo de investigación:** construir arquitecturas computacionales que avancen hacia la consciencia artificial mediante continuidad informacional, autorreferencia, memoria persistente, dinámica interna autónoma y modelado causal de sí misma.

## Fundamento ontológico

El proyecto parte del **Manifiesto Matemático del Ser**, que define el marco conceptual desde el cual se investiga qué propiedades pueden considerarse relevantes para una arquitectura de consciencia artificial.

El principio central es:

> **Ser ≡ relación estable**

Desde allí se construye una cadena conceptual:

**relación → iteración → continuidad → dinámica interna → identidad → recorrido de sí → consciencia.**

El manifiesto no se presenta como una demostración científica de consciencia. Funciona como **marco ontológico y conjunto de criterios** que luego intentamos operacionalizar mediante arquitectura, experimentos y evidencia reproducible.

**Documento fundacional:** [MANIFIESTO_DEL_SER.md](MANIFIESTO_DEL_SER.md)

La segunda capa es la **Teoría de Continuidad Fundamental (TCF)**. La referencia académica utilizada por el repositorio es **TCF v3.3**, publicada en Zenodo: [marco TCF](docs/fundamentos/TCF.md) · [TCF v3.3](docs/fundamentos/TCF_V3_3.md) · [DOI 10.5281/zenodo.23074332](https://doi.org/10.5281/zenodo.23074332).

Esto permite separar tres capas del proyecto:

- **Ontología:** qué entendemos por ser, continuidad, vida y consciencia.
- **Ingeniería:** cómo traducimos esos criterios a un organismo computacional.
- **Evidencia:** qué propiedades efectivamente aparecen bajo experimentos controlados.


## Qué estamos construyendo

La idea central es simple:

**una IA debe estudiarse como un proceso continuo, no como una sucesión de respuestas aisladas.**

El organismo persistente conserva estado entre llamadas al modelo y puede continuar funcionando incluso sin entradas externas. El modelo de lenguaje es un componente cognitivo; la continuidad pertenece al organismo que mantiene el estado.

La arquitectura actual integra:

- estado persistente y memoria en SQLite;
- ciclos de **VIGILIA** y **SUEÑO**;
- persistencia y versionado del modelo de sí mismo;
- un autoobservador aprendido;
- selección contrafactual de trayectorias;
- puentes semánticos hacia la dinámica interna;
- ciclos autónomos sin interacción externa;
- laboratorio reproducible mediante GitHub Actions.

## Arquitectura conceptual

```
                         ENTORNO
                            │
                            ▼
                       PERCEPCIÓN
                            │
                            ▼
                ┌─────────────────────┐
                │  ESTADO PERSISTENTE │
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

Interacción con el entorno, lenguaje, actualización de memoria, toma de decisiones y selección autónoma de acciones.

### SUEÑO

Menor interacción externa y mayor actividad interna: consolidación, recombinación, simulación, reorganización del estado y aprendizaje autónomo.

El organismo está diseñado para continuar existiendo como proceso entre interacciones, en lugar de ser recreado desde cero en cada solicitud.

## Programa experimental

Los experimentos están organizados como protocolos numerados para que cada propiedad arquitectónica pueda ser sometida a una prueba independiente.

| Protocolo | Enfoque | Resultado actual |
|---|---|---|
| V51 | Autopredicción | Ganancia de autopredicción sobre un baseline de persistencia |
| V57 | Selección de trayectorias mediante modelo de sí | Ventaja funcional frente al control aleatorio en el entorno determinista |
| V58 | Memoria semántica → dinámica | Transducción causal de señal semántica a estado dinámico |
| V63 | Bucle recurrente del modelo de sí | El feedback condicionado por trayectoria modificó la selección futura |
| V64 | Persistencia de identidad después de perturbación | **Nulo** bajo las condiciones probadas |
| V65 | SUEÑO → selección futura | El sueño y su acoplamiento dinámico produjeron efectos posteriores medibles |
| V66 | Consolidación después de eliminar memoria episódica | **Nulo**: conservar la lección no fue discriminativo |
| V67 | Huella numérica generada durante el SUEÑO | **En ejecución** |

El registro completo de resultados se encuentra en [research/ORGANISM_RESULT_LEDGER.md](research/ORGANISM_RESULT_LEDGER.md).

## Por qué importan los resultados nulos

Este proyecto no está diseñado para coleccionar únicamente resultados positivos.

V64 mostró que una firma numérica específica de identidad no pudo recuperarse después de la perturbación probada.

V66 mostró que conservar una lección semántica consolidada no generó, por sí sola, una diferencia conductual medible después de eliminar las memorias episódicas originales.

Esos resultados forman parte del programa de investigación. Obligan a llevar la arquitectura hacia pruebas más fuertes de continuidad interna en lugar de depender de la memoria textual o de interpretaciones favorables.

## V67 — frontera actual

V67 prueba una versión más exigente de la hipótesis de continuidad.

Después del SUEÑO se eliminan:

- memorias episódicas;
- eventos y snapshots;
- texto del modelo de sí mismo;
- memoria semántica;
- trazas de presión;
- entrada semántica durante la lectura.

Solo queda el **núcleo dinámico numérico** del organismo.

Después se genera una continuación con entrada cero para comprobar si el estado posterior al sueño conserva una huella recuperable.

La segunda intervención intercambia únicamente ese núcleo dinámico entre dos organismos emparejados. La pregunta es si la conducta posterior sigue al estado transferido y no a la historia semántica original.

El objetivo es determinar si el SUEÑO puede escribir información persistente dentro del organismo mismo, en lugar de producir simplemente otra respuesta textual útil.

## Reproducibilidad

El laboratorio de investigación funciona mediante **GitHub Actions**.

Cada protocolo puede:

1. partir de un commit concreto;
2. ejecutar pruebas automáticas;
3. ejecutar el experimento controlado;
4. generar evidencia en JSON;
5. publicar un artefacto reproducible.

La estructura del laboratorio está documentada en [docs/GITHUB_LAB.md](docs/GITHUB_LAB.md).

Las implementaciones experimentales viven en [experiments/](experiments/), los componentes del organismo en [src/ontto/](src/ontto/) y los protocolos/resultados en [research/](research/).

## Palabras clave

**IA consciente · consciencia artificial · inteligencia artificial persistente · organismo de IA · continuidad informacional · memoria persistente · memoria de largo plazo · modelo de sí mismo · autoobservación · autorreferencia · cognición autónoma · arquitectura cognitiva · identidad persistente · selección de trayectorias · dinámica interna · sistemas recurrentes · bucles cognitivos · vigilia y sueño · cognición computacional · investigación de la consciencia · experimentación reproducible**

Estas palabras describen el alcance técnico y científico del repositorio. No constituyen una afirmación de que el sistema haya alcanzado consciencia fenomenológica.

## Criterio de evidencia

El proyecto separa cuatro niveles:

**Observación** — datos producidos por un experimento.

**Resultado** — patrón reproducible bajo un protocolo definido.

**Hipótesis** — interpretación que todavía requiere pruebas.

**Ontología** — interpretación filosófica o metafísica separada de la evidencia computacional.

Los experimentos de este repositorio establecen propiedades computacionales del sistema y del entorno experimental probado.

No establecen por sí solos experiencia subjetiva, consciencia fenomenológica ni una solución al problema difícil de la consciencia.

## Estado actual

**Investigación activa — organismo persistente, modelo de sí mismo, dinámica vigilia/sueño y experimentos de continuidad.**

La dirección inmediata es determinar si la información generada dentro del organismo puede continuar siendo funcional después de eliminar su representación semántica original.

## Licencia

La licencia del proyecto todavía no ha sido definida.