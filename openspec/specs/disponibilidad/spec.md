# disponibilidad Specification

## Purpose
Definir la consulta de disponibilidad de espacios en un intervalo y los estados que bloquean el calendario.

## Requirements

### Requirement: Consultar disponibilidad
El sistema DEBE (SHALL) permitir a un usuario autenticado consultar disponibilidad de espacios para un intervalo válido. Solo reservas `APROBADA` de espacios activos bloquean el intervalo; las reservas `PENDIENTE`, `RECHAZADA` y `CANCELADA` no lo bloquean.

#### Scenario: Espacio sin conflicto
- WHEN se consulta un espacio activo para un intervalo sin reservas aprobadas solapadas
- THEN el sistema informa que el espacio está disponible

#### Scenario: Coincidencia exacta con reserva aprobada
- WHEN se consulta un intervalo idéntico al de una reserva `APROBADA` del mismo espacio
- THEN el sistema informa que el espacio no está disponible

#### Scenario: Intervalo solapado parcialmente
- WHEN el intervalo consultado se solapa parcialmente con una reserva `APROBADA` del mismo espacio
- THEN el sistema informa que el espacio no está disponible

#### Scenario: Intervalos adyacentes
- WHEN el intervalo consultado empieza exactamente cuando termina una reserva aprobada, o termina cuando empieza otra
- THEN el sistema informa que esos intervalos no se solapan

#### Scenario: Reserva pendiente en el intervalo
- WHEN el único registro coincidente del mismo espacio está en estado `PENDIENTE`
- THEN el sistema informa disponibilidad según las reservas aprobadas y no trata la solicitud pendiente como bloqueo

#### Scenario: Intervalo de consulta inválido
- WHEN el fin es igual o anterior al inicio o faltan desplazamientos horarios
- THEN el sistema rechaza la consulta con error de validación

#### Scenario: Usuario sin acceso
- WHEN una persona no autenticada consulta disponibilidad protegida
- THEN el sistema rechaza la solicitud sin revelar los datos del calendario

### Requirement: No ofrecer espacios inactivos como reservables
El sistema DEBE (SHALL) identificar un espacio inactivo en resultados y no puede informarlo como reservable aunque no existan reservas aprobadas.

#### Scenario: Consultar espacio inactivo
- WHEN un usuario consulta la disponibilidad de un espacio inactivo
- THEN el sistema informa que el espacio está inactivo y no disponible para nuevas solicitudes
