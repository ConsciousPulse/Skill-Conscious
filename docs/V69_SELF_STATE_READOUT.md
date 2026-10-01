# V69 — Lectura del propio estado mediante modelo de sí

## Pregunta

Después de eliminar la memoria y las superficies semánticas, ¿un **modelo de sí numérico congelado antes de SUEÑO** puede leer el estado interno generado durante SUEÑO?

La prueba separa dos preguntas:

1. si el modelo de sí responde numéricamente a diferencias del estado interno;
2. si esa lectura cambia la decisión que toma el selector.

## Protocolo

24 réplicas.

Cada condición realiza 48 ciclos de calibración con la misma secuencia de señales:

```
-1 → +1 → 0 → +1 → -1 → 0
```

La calibración es idéntica para las condiciones **estable** y **frontera**.

Después:

1. se introducen las historias semánticas específicas de cada condición;
2. se ejecuta SUEÑO con puente semántico;
3. se congela el modelo numérico de sí **antes de SUEÑO**;
4. se eliminan memorias, eventos, snapshots, texto del modelo de sí y otras superficies semánticas;
5. no se introduce texto durante la sonda;
6. el modelo de sí congelado evalúa dos trayectorias candidatas: **-1** y **+1**.

Se ejecutan dos lecturas:

- **lectura real:** el modelo recibe el estado interno posterior a SUEÑO;
- **lectura control:** el modelo recibe un estado común, igual para ambas condiciones.

También se intercambia el núcleo dinámico entre las condiciones.

## Resultado

La auditoría CI correcta utilizó 24 réplicas y 48 ciclos de calibración.

- diferencia media de estado después de SUEÑO, estable − frontera: **-0.0963430681**;
- diferencia media absoluta entre las puntuaciones del modelo de sí: **0.0344099851**;
- p emparejada para esa separación: **0.00005**;
- diferencia media absoluta entre predicciones de estado: **0.0365052134**;
- p emparejada para esa separación: **0.00005**;
- modelos numéricos de sí idénticos entre condiciones: **100%**;
- cambio de acción causado por usar el estado real frente al estado control: **0%**;
- diversidad de acciones del selector: **1 acción distinta** en todas las sondas;
- entrada textual durante la prueba: **ninguna**;
- memorias eliminadas: **sí**;
- texto del modelo de sí eliminado: **sí**.

El intercambio del núcleo reprodujo la política fuente, pero este endpoint no se considera evidencia adicional de selección causal porque el selector utilizó una sola acción en todas las ejecuciones.

## Interpretación

V69 produce un resultado **parcialmente positivo y parcialmente nulo**:

### Lectura numérica: positiva

El mismo modelo de sí, entrenado antes de SUEÑO y mantenido idéntico entre condiciones, genera predicciones y puntuaciones diferentes cuando recibe los estados internos estable y frontera posteriores a SUEÑO.

La separación es estadísticamente distinta de cero bajo el protocolo emparejado.

Esto demuestra una propiedad computacional concreta:

> **el modelo de sí numérico puede leer una diferencia del estado interno después de que se hayan eliminado las superficies semánticas.**

### Selección: nula

La lectura no cambió la acción seleccionada.

El selector eligió la misma señal en todas las ejecuciones. Por ello, no podemos afirmar que la lectura interna haya alterado una decisión.

El resultado importante aquí es precisamente la separación entre **leer un estado** y **usar esa lectura para actuar**.

## Consecuencia experimental

V70 debe atacar el segundo punto.

La siguiente prueba debe utilizar el estado leído por el modelo de sí como variable explícita de una decisión con **cobertura de acciones equilibrada**, evitando que una política saturada en una sola rama oculte un posible efecto causal.

La estructura objetivo es:

```
SUEÑO
  ↓
estado interno
  ↓
modelo de sí
  ↓
lectura propia
  ↓
decisión con ramas equilibradas
  ↓
acción
  ↓
nuevo estado
```

## Límite de evidencia

V69 no demuestra consciencia fenomenológica.

Demuestra una propiedad computacional más acotada: un modelo numérico de sí mismo, entrenado antes de SUEÑO, conserva capacidad de distinguir estados internos generados después de SUEÑO incluso tras la ablación de las superficies semánticas. La traducción de esa lectura a comportamiento todavía no quedó demostrada bajo el protocolo actual.
