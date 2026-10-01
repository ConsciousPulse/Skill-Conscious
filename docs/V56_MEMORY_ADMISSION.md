# V56 — Admisión de memoria compatible con el futuro

## Motivación

AEVUM define persistencia condicionada y memoria sin acumulación. V56 convierte ese principio en una política opcional de memoria del organismo.

## Política

Para cada memoria candidata:

- `coupling` es la superposición léxica con la memoria reciente más similar;
- `novelty = 1 - coupling`;
- `persistence` es la importancia declarada en [0,1];
- el operador AEVUM congelado decide si la candidata sigue siendo admisible.

El operador es:

`Omega = 1.2 * novelty - 1.0 * coupling - 0.8 * persistence`

`Omega > 0` significa admisible.

## Alcance

V56 deliberadamente no modifica el comportamiento predeterminado de memoria del organismo. Primero valida la política como adaptador determinista aislado.

## Por qué importa

El programa de consciencia no debería equiparar identidad con acumulación ilimitada. Un organismo persistente necesita una razón explícita para conservar una relación y un mecanismo igualmente explícito para permitir que material obsoleto o redundante se disuelva.

## Límite de evidencia

Este es un experimento de política de memoria. No establece consciencia.
