# Laboratorio GitHub

El laboratorio principal del proyecto se ejecuta mediante GitHub Actions. Colab queda como entorno auxiliar para análisis interactivo, visualización o experimentos que requieran intervención manual.

## Flujo reproducible

```
commit
  ↓
GitHub Actions
  ↓
tests
  ↓
experimentos
  ↓
results/*.json
  ↓
artifact de evidencia
```

## Research Lab

Workflow:

`.github/workflows/research.yml`

Se ejecuta en `push` sobre código relevante y también mediante `workflow_dispatch`.

Ejecuta:

1. tests del repositorio;
2. baseline dinámico;
3. validación de continuidad;
4. stress test longitudinal;
5. ablation de sueño;
6. recuperación de memoria;
7. manifiesto de ejecución;
8. publicación de artifacts.

Cada ejecución conserva el SHA del commit y los resultados producidos por ese código.

## Tests

Workflow:

`.github/workflows/tests.yml`

Se utiliza como chequeo de pull requests.

## Live provider smoke

Workflow:

`.github/workflows/live-provider-smoke.yml`

Es manual porque requiere secretos de un proveedor compatible con OpenAI:

- `ONTTO_API_KEY`
- `ONTTO_MODEL`
- `ONTTO_API_BASE_URL` (opcional; por defecto `https://api.openai.com/v1`)

El smoke test no pretende demostrar conciencia. Comprueba que un modelo real puede funcionar como componente cognitivo del organismo y que éste conserva trayectoria, memoria y transición WAKE/DREAM después de cerrar y reabrir el almacenamiento.

## Regla de interpretación

Los workflows pueden demostrar que un comportamiento computacional ocurrió bajo un protocolo reproducible.

No convierten automáticamente ese comportamiento en una afirmación de experiencia subjetiva. Esa distinción se mantiene explícita en los resultados.
