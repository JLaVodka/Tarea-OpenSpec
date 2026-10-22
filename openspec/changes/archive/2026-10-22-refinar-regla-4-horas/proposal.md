# Refactor de la especificación del límite de cuatro horas

## Why

Al archivar el cambio institucional, `openspec validate --all --strict` identificó que el texto normativo consolidado de `Crear solicitud válida` excede el umbral recomendado de longitud. Los escenarios y el comportamiento están especificados, pero conviene separar validación de solicitudes y límite de duración para mantener la spec legible y validable estrictamente.

## What Changes

- Se resume `Crear solicitud válida` conservando sus reglas y escenarios existentes.
- Se acorta `Limitar reservas consecutivas a cuatro horas`; sus escenarios permanecen intactos.
- No se modifica código ni comportamiento.

## Impacto

Solo cambia la redacción estructural de `solicitudes-reserva`. No requiere cambios en el plan, datos, implementación ni pruebas.
