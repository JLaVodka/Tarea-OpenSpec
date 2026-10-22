# Cancelación e historial

## Purpose

Permitir cancelaciones autorizadas y consultas acotadas de historial con evidencia de las transiciones.

## ADDED Requirements

### Requirement: Cancelar reserva
El sistema DEBE (SHALL) permitir al solicitante cancelar su reserva `PENDIENTE` o `APROBADA`, y al administrador de espacios asignado cancelarla cuando su permiso lo permita. Debe cambiar el estado a `CANCELADA`, registrar actor, fecha y motivo si se proporcionó, y liberar la franja si estaba aprobada.

#### Scenario: Solicitante cancela solicitud pendiente
- WHEN el solicitante cancela su solicitud `PENDIENTE`
- THEN el sistema la cambia a `CANCELADA` y registra el evento

#### Scenario: Solicitante cancela reserva aprobada
- WHEN el solicitante cancela su reserva `APROBADA`
- THEN el sistema la cambia a `CANCELADA`, registra el evento y libera el intervalo

#### Scenario: Usuario cancela solicitud ajena
- WHEN un estudiante o docente intenta cancelar una solicitud de otra persona sin permiso
- THEN el sistema deniega la acción y conserva el estado

#### Scenario: Cancelar solicitud rechazada o ya cancelada
- WHEN se intenta cancelar una reserva `RECHAZADA` o `CANCELADA`
- THEN el sistema rechaza la transición y preserva el estado/historial existente

#### Scenario: Cancelación por administrador fuera de ámbito
- WHEN un administrador de espacios intenta cancelar una reserva de un espacio no asignado
- THEN el sistema deniega la acción

### Requirement: Consultar historial auditado
El sistema DEBE (SHALL) registrar como eventos no editables desde la API la creación, aprobación, rechazo y cancelación de cada reserva, con actor, fecha y detalles requeridos. El solicitante consulta su historial; el administrador de espacios consulta eventos de sus espacios asignados.

#### Scenario: Consultar historial propio
- WHEN un solicitante autenticado consulta el historial de sus reservas
- THEN el sistema devuelve sus eventos en orden cronológico con estado y actor correspondientes

#### Scenario: Administrador consulta historial de espacio asignado
- WHEN un administrador de espacios consulta el historial de una reserva perteneciente a un espacio asignado
- THEN el sistema devuelve los eventos disponibles para auditoría

#### Scenario: Consultar historial fuera de ámbito
- WHEN un solicitante consulta eventos de otra persona o un administrador consulta un espacio no asignado
- THEN el sistema deniega la consulta sin exponer los eventos

#### Scenario: Intento de modificar un evento
- WHEN un usuario intenta alterar o eliminar un evento de auditoría mediante la API
- THEN el sistema deniega la operación y mantiene intacto el evento
