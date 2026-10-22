# Solicitudes de reserva

## Purpose

Definir la creación de una petición de reserva vinculada a un solicitante, espacio e intervalo.

## ADDED Requirements

### Requirement: Crear solicitud válida
El sistema DEBE (SHALL) permitir que estudiantes y docentes autenticados creen una solicitud para sí mismos en un espacio activo, con fechas ISO 8601 que incluyan desplazamiento horario y un intervalo de duración positiva. La solicitud se crea con estado `PENDIENTE`.

#### Scenario: Solicitud válida
- WHEN un estudiante o docente solicita un espacio activo con inicio futuro y fin posterior al inicio
- THEN el sistema guarda la solicitud como `PENDIENTE`, vinculada al actor autenticado

#### Scenario: Fin igual o anterior al inicio
- WHEN el intervalo solicitado tiene fin igual o anterior al inicio
- THEN el sistema rechaza la solicitud con error de validación y no crea reserva

#### Scenario: Fecha de inicio pasada
- WHEN el inicio solicitado es anterior al momento actual
- THEN el sistema rechaza la solicitud y explica que el inicio debe ser futuro

#### Scenario: Fecha sin desplazamiento horario
- WHEN el inicio o el fin se envía sin zona/desplazamiento horario
- THEN el sistema rechaza los datos ambiguos y no crea reserva

#### Scenario: Solicitud para espacio inactivo
- WHEN un estudiante o docente solicita un espacio inactivo
- THEN el sistema rechaza la solicitud y explica que el espacio no está reservable

#### Scenario: Solicitante intenta crear para otra persona
- WHEN un usuario incluye otro identificador como solicitante sin permiso explícito para actuar en nombre de terceros
- THEN el sistema deniega la operación o rechaza el campo y no atribuye la solicitud a otra persona

### Requirement: Consultar solicitudes
El sistema DEBE (SHALL) permitir a cada solicitante consultar sus propias solicitudes y a un administrador de espacios consultar las solicitudes de espacios asignados; no debe revelar solicitudes fuera de ese ámbito.

#### Scenario: Solicitante consulta la propia solicitud
- WHEN una persona autenticada consulta una solicitud propia
- THEN el sistema devuelve sus datos y estado actual

#### Scenario: Solicitante consulta solicitud ajena
- WHEN una persona consulta una solicitud perteneciente a otro usuario sin permiso administrativo
- THEN el sistema deniega la consulta sin revelar datos de la solicitud

#### Scenario: Administrador consulta solicitud de espacio asignado
- WHEN un administrador de espacios consulta una solicitud asociada a un espacio que administra
- THEN el sistema devuelve la solicitud para su revisión
