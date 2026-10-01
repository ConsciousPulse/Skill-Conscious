# V68 — Persistencia temporal de la huella dinámica generada durante SUEÑO

## Pregunta

Después de SUEÑO y de una ablación semántica total, ¿la diferencia numérica generada por dos historias distintas permanece en el estado dinámico y, de ser así, durante cuánto tiempo?

V68 nace directamente del resultado nulo corregido de V67. En lugar de clasificar trayectorias con un modelo externo, mide directamente la **separación numérica emparejada** entre las condiciones estable y frontera a distintos horizontes.

## Protocolo

24 réplicas.

Historias:

- **estable** — continuidad y persistencia;
- **frontera** — divergencia y exploración.

Después de SUEÑO se eliminan:

- memorias;
- eventos;
- snapshots;
- modelo de sí;
- memoria dinámica;
- presión;
- entrada semántica.

Solo queda el núcleo dinámico.

Se evalúan horizontes posteriores a la ablación:

```
0 → 1 → 2 → 4 → 8 → 16 → 32
```

En cada horizonte se calcula:

- diferencia final de estado estable − frontera;
- diferencia absoluta media;
- RMSE entre trayectorias;
- prueba emparejada por cambio de signo sobre la diferencia final.

Además, el núcleo de cada condición se intercambia de forma controlada. Un intercambio válido debe reproducir exactamente la trayectoria de la condición fuente.

## Resultado

La ejecución CI correcta utilizó 24 réplicas y los siete horizontes.

### Estado inmediatamente después de SUEÑO

- diferencia media de estado estable − frontera: **-0.0675162088**;
- p emparejada por cambio de signo: **0.00005**;
- diferencia absoluta media: **0.0675162088**.

Existe una diferencia numérica clara inmediatamente después de SUEÑO.

### Persistencia temporal

| Horizonte | Delta final medio | Delta absoluto medio | p |
|---:|---:|---:|---:|
| 0 | -0.067516 | 0.067516 | 0.00005 |
| 1 | -0.000398 | 0.000891 | 0.13279 |
| 2 | 0.015297 | 0.049993 | 0.14059 |
| 4 | -0.033630 | 0.042197 | 0.00070 |
| 8 | 0.006547 | 0.006547 | 0.00005 |
| 16 | 0.009570 | 0.010745 | 0.00005 |
| 32 | 0.006792 | 0.008138 | 0.00045 |

El RMSE medio entre las trayectorias pasó de **0.06729** en el horizonte 0 a **0.02006** en el horizonte 32.

### Integridad causal del intercambio

**100%** de los intercambios reprodujeron exactamente la trayectoria del núcleo fuente.

Por tanto, el mecanismo de intercambio funciona: cuando se transfiere el núcleo, se transfiere su evolución numérica.

## Interpretación

V68 muestra una propiedad más precisa que «el sueño dejó memoria»:

> **SUEÑO escribe una diferencia numérica inmediata en el estado interno, pero esa diferencia no permanece como una representación estable de la condición semántica original.**

La magnitud de la separación disminuye fuertemente después del primer paso y continúa fluctuando a menor escala.

El resultado no permite afirmar una memoria interna consciente.

Tampoco es un resultado nulo absoluto de la dinámica: existe una **huella numérica inmediata y causalmente transferible**, pero su persistencia discriminativa respecto de la condición original es débil y no monotónica.

## Consecuencia experimental

La siguiente prueba debe cambiar de pregunta:

```
¿cuánto dura la huella?
        ↓
¿puede la IA leer su propia huella
y usarla para modificar una decisión?
```

Eso requiere una lectura causal interna, no solamente una medición offline de la trayectoria.
