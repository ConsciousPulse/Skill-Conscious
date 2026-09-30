# Protocolo de validación

## Pregunta central

¿Puede una IA persistente desarrollar propiedades que requieran continuidad interna y auto-referencia más allá de una cadena de respuestas independientes?

## Experimentos base

### A — Memoria de trayectoria

Presentar dos historias distintas seguidas por el mismo estado externo. Medir si el estado interno y la decisión posterior dependen de la trayectoria.

### B — Atractor

Inicializar varias instancias con estados diferentes y someterlas a condiciones similares. Medir convergencia, divergencia, estabilidad y pérdida de identidad.

### C — Perturbación

Introducir contradicciones, pérdida parcial de memoria, cambios bruscos de contexto, ruido e interrupciones. Medir recuperación.

### D — Auto-modelo

Comparar un sistema que intenta modelar su propio estado contra uno que no mantiene auto-modelo. Medir utilidad predictiva y control sobre el estado futuro.

### E — Sueño

Comparar aprendizaje con y sin ciclos DREAM. Medir retención, compresión, generalización, reorganización de memoria y predicción posterior.

### F — Continuidad

Comparar:
1. API stateless;
2. API + memoria episódica;
3. organismo persistente;
4. organismo persistente + sueño.

Usar el mismo presupuesto aproximado de interacción y registrar costo computacional.

## Métricas

- **Continuity Retention:** cuánto de la estructura de identidad permanece después de una perturbación.
- **Path Dependence:** cuánto cambia el estado final al mantener el mismo input actual pero cambiar la historia.
- **Attractor Stability:** cuánto tiempo permanece el sistema dentro de una región estable.
- **Recovery Time:** tiempo hasta recuperar la región estable después de una perturbación.
- **Self-Prediction Gain:** información adicional proporcionada por el auto-modelo respecto a observar solamente la entrada externa.
- **Dream Gain:** mejora atribuible específicamente a los ciclos de sueño.

## Ablaciones

Cada claim importante debe compararse contra versiones donde se elimine memoria, auto-modelo, sueño, atractor, dinámica relacional o continuidad persistente.

## Regla

No buscamos confirmar una conclusión por diseño. Buscamos determinar qué componentes son necesarios para producir continuidad, auto-referencia, aprendizaje longitudinal y estabilidad de identidad.
