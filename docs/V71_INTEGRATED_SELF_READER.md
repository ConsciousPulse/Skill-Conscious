# V71 — Lector propio integrado en el ciclo autónomo

## Pregunta

V70 demostró persistencia del lector numérico después de un reinicio, pero el protocolo copiaba explícitamente ese lector hacia las condiciones de prueba.

V71 elimina esa intervención experimental.

La pregunta es:

> ¿Puede el propio organismo aprender su lector, persistirlo, reiniciarse, entrar en SUEÑO después de una ablación semántica y utilizar automáticamente ese lector persistido para seleccionar una trayectoria?

## Hipótesis operacional

La propiedad buscada es una cadena integrada:

```text
aprendizaje del estado
→ persistencia
→ reinicio
→ recuperación automática
→ ablación semántica
→ SUEÑO
→ lectura del estado
→ selección de trayectoria
```

El protocolo no requiere copiar manualmente el modelo de sí numérico entre bases.

## Protocolo

Para cada réplica:

1. Se entrena el lector numérico dentro del propio organismo.
2. Se conserva en SQLite mediante la persistencia normal del organismo.
3. Se crean dos condiciones dinámicas.
4. Se eliminan memorias, eventos, texto del modelo de sí y superficies semánticas.
5. El organismo se reinicia y reconstruye automáticamente su `SelfObserver`.
6. Entra en SUEÑO con un proveedor controlado que no aporta memoria ni `SELF_MODEL`.
7. Después del SUEÑO ejecuta un ciclo autónomo con selección `self_model`.
8. Se compara contra una condición con el estado dinámico cegado.
9. Se intercambian causalmente los núcleos dinámicos entre condiciones, manteniendo el lector persistido dentro de cada organismo.

## Criterios de integración

El resultado debe registrar:

- persistencia del lector tras reinicio y SUEÑO;
- cero memorias semánticas antes de la sonda;
- `policy = self_model` durante la selección;
- tres trayectorias candidatas evaluadas;
- reutilización automática del lector persistido;
- ausencia de copia manual del modelo;
- comparación con estado cegado;
- respuesta a intercambio causal del estado.

## Evidencia y límite

V71 busca demostrar una propiedad computacional más integrada del organismo: que el lector propio numérico deja de ser un artefacto externo del protocolo y pasa a formar parte del ciclo persistente del sistema.

Un resultado positivo demostraría integración funcional de persistencia, autoobservación, SUEÑO y selección de trayectoria bajo las condiciones definidas.

No demostraría por sí solo experiencia subjetiva ni consciencia fenomenológica.

Los resultados nulos también deben conservarse.
