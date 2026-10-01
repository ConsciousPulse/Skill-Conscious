# Colab

## Experimento 01

Abrir el [cuaderno de referencia de continuidad](https://colab.research.google.com/github/chrishotza/Consciencia-Skill/blob/main/notebooks/01_continuity_baseline.ipynb).

Clona el repositorio público y ejecuta el motor relacional actual.

## Experimento 02

El cuaderno de API en vivo utiliza un proveedor LLM real y estado persistente en SQLite.

Colab se utiliza como laboratorio, no como anfitrión permanente 24/7. Un organismo continuo necesita un entorno de ejecución persistente fuera de los límites normales de las sesiones de cuaderno.

## Secretos

Guardar las credenciales de API en **Colab Secrets**. Nunca subir claves a GitHub.

Requeridos:

- `ONTTO_API_KEY`
- `ONTTO_MODEL`

Opcionales:

- `ONTTO_API_BASE_URL`
- `ONTTO_AGENT_ID`

## Evidencia

Cada ejecución en vivo debe conservar:

- semilla y configuración;
- modelo y proveedor;
- ciclos de VIGILIA;
- ciclos de SUEÑO;
- snapshots del estado;
- memorias;
- telemetría de tokens/costo cuando el proveedor la exponga.
