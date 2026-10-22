# prevencion-reservas-simultaneas Specification

## Purpose
Evitar que dos reservas incompatibles del mismo espacio queden aprobadas, también cuando las operaciones ocurren simultáneamente.

## Requirements

### Requirement: Detectar solapamiento
El sistema DEBE (SHALL) considerar solapados dos intervalos semiabiertos `[inicio, fin)` del mismo espacio cuando `nuevo_inicio < existente_fin AND existente_inicio < nuevo_fin`. Una coincidencia exacta cuenta como solapamiento; los intervalos adyacentes no.

#### Scenario: Rechazar intervalo idéntico
- WHEN una solicitud intenta aprobarse en el mismo espacio y con inicio y fin idénticos a otra reserva aprobada
- THEN el sistema rechaza la aprobación por conflicto

#### Scenario: Rechazar solapamiento parcial
- WHEN una solicitud aprobada se solapa parcialmente con otra reserva aprobada del mismo espacio
- THEN el sistema rechaza la nueva aprobación y conserva la reserva anterior

#### Scenario: Permitir intervalos adyacentes
- WHEN una solicitud empieza exactamente al terminar una reserva aprobada del mismo espacio
- THEN el sistema puede aprobarla porque los intervalos no se solapan

#### Scenario: Permitir mismo intervalo en espacios distintos
- WHEN dos solicitudes con el mismo intervalo corresponden a espacios diferentes
- THEN la existencia de una aprobación en un espacio no bloquea la aprobación del otro

#### Scenario: Reintentar aprobación tras cancelar conflicto
- WHEN la única reserva que causaba conflicto está `CANCELADA` antes de la nueva aprobación
- THEN el sistema puede aprobar la nueva solicitud si no hay otro conflicto

### Requirement: Comprobar y escribir atómicamente
El sistema DEBE (SHALL) comprobar conflictos y cambiar la solicitud a `APROBADA` en una operación atómica que impida aprobar dos reservas solapadas del mismo espacio ante solicitudes concurrentes.

#### Scenario: Dos solicitudes concurrentes incompatibles
- WHEN dos operaciones simultáneas intentan aprobar intervalos solapados para el mismo espacio
- THEN como máximo una queda `APROBADA` y la otra recibe un conflicto explícito

#### Scenario: Error durante la aprobación
- WHEN ocurre un error antes de completar la transacción de aprobación
- THEN la transacción no deja una aprobación parcial ni un estado incoherente

#### Scenario: Administrador sin ámbito
- WHEN un administrador de espacios intenta aprobar una solicitud de un espacio que no tiene asignado
- THEN el sistema deniega la acción sin cambiar estados
