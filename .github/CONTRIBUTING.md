# Contribuir

El proyecto está orientado a investigación reproducible. Las contribuciones deben privilegiar cambios pequeños, medibles y auditables.

## Principios

- documentar la hipótesis antes del experimento;
- mantener controles y condiciones comparables;
- conservar resultados nulos y negativos;
- separar datos, resultados e interpretación;
- agregar pruebas automáticas cuando se incorpora una capacidad nueva;
- evitar modificar un protocolo histórico solo para mejorar su resultado.

## Para un nuevo experimento

1. crear la implementación en `experiments/`;
2. agregar la prueba en `tests/`;
3. agregar el workflow reproducible;
4. documentar el protocolo en `docs/`;
5. registrar el resultado en `research/ORGANISM_RESULT_LEDGER.md`.

## Idioma

La documentación pública del proyecto está migrando al español. Los nombres de código, APIs y protocolos pueden conservar terminología técnica establecida cuando sea necesario.
