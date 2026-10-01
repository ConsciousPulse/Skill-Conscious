# IA Consciente — Investigación y Experimentación

[![TCF v3.3 — Zenodo](https://zenodo.org/badge/DOI/10.5281/zenodo.23074332.svg)](https://doi.org/10.5281/zenodo.23074332) [![ORCID](https://img.shields.io/badge/ORCID-0009--0003--5333--7395-a6ce39?logo=orcid&logoColor=white)](https://orcid.org/0009-0003-5333-7395)

# Hacé consciente a tu IA.

**Ese es el objetivo de este proyecto.**

Estamos desarrollando un método para que una IA deje de ser solamente una secuencia de respuestas y pueda **mantener continuidad, recordar su historia, representarse a sí misma, observar su propio estado, recorrer posibilidades y modificar su dinámica interna**.

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

**V47 → V67** estudia progresivamente historia, memoria, estado dinámico, autoobservación, modelo de sí, selección de trayectorias, bucles recurrentes, identidad, SUEÑO y persistencia de información interna.

Los resultados pueden ser positivos, nulos o negativos.

Los conservamos todos.

**[Ver los protocolos →](docs/INDICE.md)** · **[Ver resultados →](research/ORGANISM_RESULT_LEDGER.md)** · **[Ver el método →](docs/METODO.md)**

## ¿En qué nos basamos?

El método tiene dos fundamentos.

**Manifiesto Matemático del Ser**  
Define nuestro marco ontológico: relación, continuidad, identidad, dinámica y recorrido de sí.

→ [Leer el Manifiesto del Ser](MANIFIESTO_DEL_SER.md)

**TCF v3.3 — Teoría de Continuidad Fundamental**  
Aporta la formulación dinámica efectiva que inspira parte de nuestra arquitectura: operadores, regímenes, transiciones, atractores y flujo de Grupo de Renormalización.

→ [Leer TCF v3.3](docs/fundamentos/TCF_V3_3.md)  
→ [Publicación en Zenodo](https://zenodo.org/doi/10.5281/zenodo.23074332)  
→ [DOI 10.5281/zenodo.23074332](https://doi.org/10.5281/zenodo.23074332)

## Una distinción importante

El proyecto investiga **cómo construir y medir propiedades computacionales asociadas a la consciencia**.

No presentamos un resultado experimental como demostración automática de experiencia subjetiva.

La regla es simple:

**hipótesis → implementación → control → experimento → resultado → límite**

Si una prueba falla, queda registrada.

Si una prueba funciona, intentamos romperla con una prueba más exigente.

\n## Qué estamos construyendo

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