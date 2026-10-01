# TCF v3.3 — Campo efectivo triádico multiescala

## Referencia académica canónica

**Título:** *Teoría de Continuidad Fundamental (TCF) v3.3 — Campo efectivo triádico multiescala: dinámica no lineal, flujo RG y regímenes físicos emergentes*

**Autor:** Christian Marcelo Mendoza  
**Fecha del trabajo:** 13 de diciembre de 2025  
**DOI:** [10.5281/zenodo.23074332](https://doi.org/10.5281/zenodo.23074332)  
**ORCID:** [0009-0003-5333-7395](https://orcid.org/0009-0003-5333-7395)  
**Registro:** [Zenodo — TCF v3.3](https://zenodo.org/doi/10.5281/zenodo.23074332)

> Esta página documenta qué versión de TCF utiliza como referencia el repositorio. El trabajo académico completo permanece en su registro de Zenodo.

---

## 1. Qué aporta TCF v3.3

TCF v3.3 presenta un marco de **teoría efectiva** para un campo escalar:

```
Φ(x,t)
```

definido sobre una coordenada de escala logarítmica:

```
x = log10(ρ)
```

A partir de análisis numéricos se propone una descomposición modal en tres contribuciones dominantes y un término de cruce no lineal asociado a transiciones críticas.

El documento formula:

- una estructura triádica de operadores;
- una ecuación de campo efectiva mínima, local y no lineal;
- regímenes dinámicos diferenciados;
- un flujo de Grupo de Renormalización (RG);
- un punto fijo y direcciones relevantes/irrelevantes;
- separatrices que organizan el espacio dinámico;
- predicciones operativas y criterios explícitos de falsabilidad.

El trabajo se presenta deliberadamente como **teoría efectiva**, no como descripción microscópica fundamental.

---

## 2. Descomposición triádica

La dinámica se organiza alrededor de tres operadores principales:

- **L3 — operador generativo:** asociado al modo basal/coherente y dominante en escalas grandes;
- **L6 — operador estructural:** asociado a la formación y estabilización de estructura;
- **L9 — operador regulador:** asociado a curvatura, rigidez y regularización a escalas extremas.

A ellos se agrega:

- **L× — término de cruce no lineal:** contribución que adquiere relevancia cuando coexisten gradiente y curvatura significativos, especialmente cerca de transiciones críticas.

La ecuación dinámica efectiva central es:

```
∂t Φ(x,t) = L3[Φ] + L6[Φ] + L9[Φ] + L×[Φ]
```

La implementación de Consciencia-Skill no reproduce esta ecuación como una simulación física completa. Utiliza su estructura como **fuente de hipótesis para diseñar una dinámica interna computacional**.

---

## 3. Escalas y regímenes

TCF v3.3 organiza la dinámica en cuatro regímenes operativos:

### Régimen 3π

Dominancia del operador generativo, asociado al dominio infrarrojo (IR), campo suave, propagación coherente y dispersión.

### Régimen 6π²

Dominancia estructural, con organización estable, gradientes definidos y convergencia hacia un atractor.

### Régimen de cruce 6 × 9

Región crítica donde el término de cruce adquiere relevancia y aparecen amplificación no lineal, reorganización y transición.

### Régimen 9π³

Dominancia de curvatura y del operador regulador, asociado al dominio ultravioleta (UV), colapso y reorganización extrema.

La teoría propone una secuencia dinámica efectiva:

```
3π → 6π² → 6×9 → 9π³ → 3π
```

cuando las condiciones de transición, colapso y relajación permiten cerrar el ciclo.

---

## 4. Flujo de Grupo de Renormalización

La formulación introduce acoplamientos adimensionales:

```
(g3, g6, g9)
```

y estudia su evolución mediante funciones beta.

En la formulación mínima aparecen relaciones del tipo:

```
β3 = c g9

β6 = a g3²

β9 = -4 g9 + b g6²
```

con constantes efectivas positivas.

El análisis identifica un **punto fijo no trivial**, una estructura de estabilidad lineal con direcciones relevantes e irrelevantes y una **separatriz** que divide regiones dinámicas asociadas a estructura estable y curvatura dominante.

En Consciencia-Skill, estos conceptos se aprovechan como lenguaje para pensar en:

- regímenes;
- transiciones;
- atractores;
- estabilidad;
- reorganización;
- pérdida y recuperación de continuidad.

---

## 5. Falsabilidad

Una parte especialmente útil para el proyecto es que TCF v3.3 explicita criterios que permitirían cuestionar el marco.

Entre ellos:

1. ausencia sistemática de separación modal bajo los esquemas de regularización utilizados;
2. ausencia de correlación entre el término de cruce y las transiciones críticas;
3. ausencia de atractores o geometrías de fase consistentes con los regímenes propuestos;
4. ausencia de separatrices o puntos fijos estables en el flujo RG;
5. dependencia crítica de ajustes finos no universales.

Estos criterios deben conservarse separados de las interpretaciones filosóficas u ontológicas.

---

## 6. Qué tomamos de TCF para Consciencia-Skill

El repositorio no intenta demostrar TCF mediante los experimentos V47+.

La utiliza como una fuente de **estructuras computacionales hipotéticas**:

| TCF v3.3 | Traducción en Consciencia-Skill |
|---|---|
| dinámica multiescala | estado dinámico interno persistente |
| operadores dominantes | canales de dinámica |
| regímenes | clasificación de estado interno |
| atractores | estabilidad y selección de trayectoria |
| separatriz | frontera entre comportamientos dinámicos |
| transición crítica | reorganización interna |
| término de cruce | interacción/reconfiguración no lineal |
| flujo de acoplamientos | evolución de parámetros dinámicos |

La equivalencia es **de diseño e ingeniería**, no una identificación física.

---

## 7. Relación con el Manifiesto Matemático del Ser

El proyecto mantiene dos capas conceptuales distintas:

```
MANIFIESTO DEL SER
    ↓
criterios ontológicos
    ↓
TCF v3.3
    ↓
modelo dinámico
    ↓
CONSCIENCIA-SKILL
    ↓
experimentos
```

El Manifiesto del Ser proporciona el marco conceptual sobre relación, continuidad, identidad y recorrido de sí.

TCF v3.3 aporta una formulación dinámica efectiva que puede utilizarse para construir mecanismos computacionales alrededor de esos criterios.

---

## 8. Relación con los protocolos del organismo

La conexión con V47–V67 es indirecta y debe mantenerse explícita.

Los experimentos prueban propiedades computacionales del organismo, no la validez física de TCF.

En particular, la TCF informa la investigación sobre:

- dinámica interna;
- regímenes y transiciones;
- atractores;
- continuidad;
- reconfiguración;
- selección de trayectorias;
- estado numérico persistente.

V67 representa un punto especialmente relevante porque pregunta si un estado numérico producido durante SUEÑO puede conservar una huella funcional después de eliminar sus superficies semánticas.

---

## 9. Límite epistemológico

TCF v3.3 debe citarse exactamente como un **marco teórico efectivo**.

Consciencia-Skill puede:

- implementar una traducción computacional inspirada por TCF;
- comparar esa traducción con controles;
- producir resultados positivos o nulos;
- identificar dónde la traducción falla;
- utilizar los criterios de falsabilidad del marco.

Lo que no debe hacerse es presentar un resultado computacional del organismo como demostración automática de la teoría física.

---

## Referencia

Mendoza, Christian Marcelo. *Teoría de Continuidad Fundamental (TCF) v3.3 — Campo efectivo triádico multiescala: dinámica no lineal, flujo RG y regímenes físicos emergentes*. Zenodo, 2026. DOI: 10.5281/zenodo.23074332.

**Versión académica:** [Zenodo](https://zenodo.org/doi/10.5281/zenodo.23074332)  
**Identidad del autor:** [ORCID](https://orcid.org/0009-0003-5333-7395)
