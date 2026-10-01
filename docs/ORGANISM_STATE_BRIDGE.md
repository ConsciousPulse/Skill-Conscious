# Puente entre el organismo y el estado dinámico

## Propósito

El organismo persistente ahora transporta un pequeño estado numérico explícito junto con la capa de memoria y eventos textuales.

Esta es una capa de integración, no una afirmación de que el estado numérico sea un modelo de la experiencia subjetiva.

## Estado

El estado persistente del organismo incluye:

- `dynamic_state`
- `dynamic_prev_state`
- `dynamic_memory`
- `dynamic_pressure`
- `dynamic_attractor_distance`
- `dynamic_last_input`
- `dynamic_steps`

La memoria textual existente, el registro de eventos, el modelo de sí y los contadores de VIGILIA/SUEÑO permanecen separados.

## Transición

El puente utiliza la misma función de transición de `src/ontto/dynamics.py` que ya emplean los experimentos de investigación.

Para una señal externa explícita de vigilia `u`, la transición es:

```
x[t+1] = F(x[t], m[t], p[t], u[t])
```

El puente avanza la dinámica desde el estado persistido y escribe el nuevo estado en SQLite.

La semilla aleatoria se deriva de:

```
dynamic_seed + dynamic_steps + local_step_offset
```

de modo que un reinicio no vuelve a cero la secuencia determinista de ruido de la trayectoria dinámica.

## Política de señales

La política predeterminada es deliberadamente simple:

- interacción externa durante VIGILIA: +1.0
- ciclo autónomo: 0.0
- SUEÑO: 0.0

Esto no constituye una codificación semántica del lenguaje. Es una señal controlada de evento/régimen utilizada para conectar el organismo persistente real con el mismo núcleo dinámico estudiado en V43–V46.

Cambiar esta política constituye un experimento futuro y debe tratarse como un protocolo separado.

## Qué habilita

El estado dinámico forma parte de la ontología serializada del organismo, por lo que queda visible para el contexto del LLM. Esto crea el primer puente directo entre:

```
organismo LLM
    ↕
estado persistente SQLite
    ↕
dinámica de investigación
```

## Comportamiento 24/7

`autonomous_wake_cycle()` ya está implementado. Esto cierra una brecha previa en `PersistentOrganism.run()` y `run_daemon.py`, que ya esperaban ese método cuando no había entrada externa disponible.

El ciclo autónomo realiza un avance dinámico de entrada cero y registra el resultado como evento de VIGILIA/autónomo.

## Próxima etapa experimental

La siguiente etapa no consiste en afirmar consciencia. Consiste en medir si un organismo persistente real respaldado por un LLM desarrolla propiedades de trayectoria análogas a las ya estudiadas en el simulador:

- retención de historia;
- recuperación después de perturbaciones;
- autopredicción;
- efectos de historia bajo sonda común;
- efectos de intervención sobre la memoria;
- diferencias entre VIGILIA y SUEÑO.
