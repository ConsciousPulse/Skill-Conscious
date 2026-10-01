# Protocolo longitudinal del organismo v1

## Objetivo

Medir si un organismo real respaldado por un LLM y con estado persistente mantiene una trayectoria observable a través de ciclos repetidos de **VIGILIA**, **SUEÑO**, ciclos autónomos y un reinicio del proceso.

Este protocolo mide observables de ingeniería. No considera que la persistencia, la memoria o la autorreferencia sean evidencia suficiente de consciencia subjetiva.

## Secuencia central

El protocolo acotado repite:

```
estímulo
  ↓
VIGILIA
  ↓
actualización del estado dinámico
  ↓
SUEÑO o ciclo autónomo
  ↓
persistencia SQLite
  ↺
```

Después de completar los ciclos solicitados, SQLite se cierra y se vuelve a abrir. A continuación se ejecuta un ciclo adicional de **VIGILIA** a partir del estado recuperado.

## Observables registrados

Cada avance dinámico escribe una fila en `dynamic_snapshots` que contiene:

- régimen;
- intervalo de pasos;
- señal de entrada;
- estado previo;
- estado;
- memoria dinámica;
- presión;
- distancia al atractor;
- marca temporal.

El protocolo también registra:

- eventos persistentes;
- memorias textuales;
- versión del modelo de sí;
- contador de arranques;
- contadores acumulados de VIGILIA/SUEÑO;
- huellas de trayectoria/estado.

## Modos

### fake

Proveedor determinista utilizado para CI y auditorías de instrumentación.

### live

Utiliza el proveedor compatible con OpenAI configurado mediante:

- `ONTTO_API_KEY`
- `ONTTO_MODEL`
- `ONTTO_API_BASE_URL` (opcional)

El modo `live` es la ejecución científicamente relevante del organismo. El modo `fake` solo comprueba que el protocolo de instrumentación y persistencia funcione.

## Ejecución de 24 horas

El script está acotado por cantidad de ciclos y duración entre ciclos, en lugar de codificar un bucle fijo de 24 horas.

Para una observación real de 24 horas, elegir un período adecuado al estudio, ejecutar el script con el `--sleep-seconds` correspondiente y conservar tanto la base de datos SQLite completa como la evidencia JSON.

GitHub Actions no debe utilizarse como anfitrión de una ejecución de 24 horas basada en reloj de pared. El organismo persistente debe ejecutarse en un host local o servidor persistente.

## Primera ejecución en vivo recomendada

Utilizar:

```
python experiments/longitudinal_organism_v1.py --mode live --cycles 40 --dream-every 10
```

Esto proporciona una primera ejecución longitudinal acotada antes de comprometer una observación de jornada completa.

Una ejecución de jornada completa debe conservar la misma configuración del protocolo y modificar únicamente el horizonte de observación.
