# Aprobación y rechazo

## Purpose

Definir la decisión administrativa que lleva una solicitud pendiente a aprobada o rechazada.

## ADDED Requirements

### Requirement: Aprobar solicitud pendiente
El sistema DEBE (SHALL) permitir al administrador de espacios asignado aprobar una solicitud `PENDIENTE` únicamente si el espacio sigue activo y no hay una reserva aprobada solapada. Debe registrar decisor y fecha.

#### Scenario: Aprobación válida
- WHEN el administrador asignado aprueba una solicitud pendiente de un espacio activo sin conflicto
- THEN el sistema cambia su estado a `APROBADA` y registra actor y momento de decisión

#### Scenario: Rechazar transición desde estado final
- WHEN un administrador intenta aprobar una solicitud `RECHAZADA`, `CANCELADA` o ya `APROBADA`
- THEN el sistema rechaza la transición y conserva el estado existente

#### Scenario: Espacio inactivo al aprobar
- WHEN un administrador intenta aprobar una solicitud cuyo espacio ahora está inactivo
- THEN el sistema rechaza la aprobación y explica el motivo

#### Scenario: Administrador de espacio no asignado
- WHEN un administrador de espacios intenta decidir una solicitud fuera de su ámbito
- THEN el sistema deniega la operación sin cambiar la solicitud

#### Scenario: Administrador de sistema sin rol de espacios
- WHEN un usuario con solo el rol `ADMIN_SISTEMA` intenta aprobar una solicitud
- THEN el sistema deniega la operación

### Requirement: Rechazar con motivo
El sistema DEBE (SHALL) permitir al administrador de espacios asignado rechazar una solicitud `PENDIENTE` únicamente con un motivo que no quede vacío al quitar espacios externos, y registrar actor, momento y motivo.

#### Scenario: Rechazo con motivo
- WHEN el administrador asignado rechaza una solicitud pendiente con motivo no vacío
- THEN el estado cambia a `RECHAZADA` y el motivo queda asociado al evento de decisión

#### Scenario: Rechazo sin motivo
- WHEN el administrador intenta rechazar sin motivo o con texto vacío/compuesto solo por espacios
- THEN el sistema rechaza la transición y mantiene el estado `PENDIENTE`

#### Scenario: Rechazo repetido
- WHEN un administrador intenta rechazar una solicitud que ya no está pendiente
- THEN el sistema rechaza la transición y conserva el historial previo
