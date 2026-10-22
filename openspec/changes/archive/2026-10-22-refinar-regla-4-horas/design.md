# Diseño del refactor de la spec

La regla de duración queda en `Limitar reservas consecutivas a cuatro horas`; la validación de existencia, fechas, espacio activo y solapamientos queda en `Crear solicitud válida`. Se conservan todos los escenarios de ambas capacidades y la implementación no cambia.

## Decisión

Se reduce el texto de cada requisito a una obligación principal y se mantienen los detalles verificables en `#### Scenario:`. Se descarta dejar el texto extenso y aceptar la advertencia, porque `openspec validate --all --strict` debe pasar con las specs archivadas.
