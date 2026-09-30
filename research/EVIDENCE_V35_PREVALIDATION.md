# V35 — Metric Robustness Pre-validation

## Estado

**PRE-VALIDACIÓN LOCAL DEL COMMIT.**  
Este documento no sustituye un artefacto de GitHub Actions. Los números de abajo provienen de un espejo local del código V35 ejecutado con las mismas ecuaciones del repositorio, las mismas semillas y el mismo esquema de ruido de NumPy. El resultado debe contrastarse con el artefacto oficial de Actions cuando ese run quede accesible.

## Resultado

La réplica usa historia-seeds 100–109, seis puntos paramétricos, cuatro pares históricos, nueve contextos memoria×presión, ángulos 30° y 150°, radio 1.1, entrada futura exactamente cero, cinco semillas independientes de referencia y cinco de prueba.

La inferencia se realiza sobre 40 bloques history-seed, con sign-flip estratificado por los cuatro pares históricos (20.000 permutaciones) y bootstrap estratificado (10.000 réplicas).

| Métrica | Contraste 30°−150° | Null 95% | p | IC bootstrap 95% |
|---|---:|---:|---:|---:|
| signed_affinity | **0.222068** | 0.064359 | **0.00005** | **[0.206720, 0.236939]** |
| distance_margin | **1.013096** | 0.292202 | **0.00005** | **[0.936911, 1.086535]** |
| cosine_delta | **0.580340** | 0.166926 | **0.00005** | **[0.530877, 0.628016]** |

Las tres métricas mantienen el mismo contraste direccional. En el nivel de celdas agregadas, la fracción de contrastes positivos fue aproximadamente 87% para las tres lecturas.

Las tres mediciones están relacionadas, pero no son idénticas: las correlaciones entre los contrastes por celda fueron 0.973 para signed-affinity vs distance-margin, 0.964 para distance-margin vs cosine-delta y 0.886 para signed-affinity vs cosine-delta.

## Lectura

El hallazgo de esta pre-validación es que la separación angular no parece depender exclusivamente de la fórmula normalizada de signed-affinity. Una diferencia de distancia sin normalizar y una diferencia de similitud coseno reproducen el mismo signo agregado sobre los 40 bloques históricos.

Esto refuerza una interpretación de **estructura geométrica/dinámica computacional reproducible** bajo el protocolo.

No demuestra conciencia, experiencia subjetiva, sentiencia ni una propiedad fuera del simulador.

## Próximo control

El siguiente paso lógico es V36: **leave-one-history-pair-out**, para comprobar que el efecto agregado no esté dominado por ninguno de los cuatro tipos de historia utilizados en el diseño.

## Reproducibilidad

Código V35: `df03be07ad8b6f792b76a9fb6aedf4af677d97a9`

Workflow V35: `f977887a710b988b4187f5cbb3e2d50e52f7f024`

Fuente de la pre-validación: ejecución local del commit, con ruido pre-generado mediante `numpy.random.default_rng(seed)` y el mismo índice temporal de la implementación de `simulate`.
