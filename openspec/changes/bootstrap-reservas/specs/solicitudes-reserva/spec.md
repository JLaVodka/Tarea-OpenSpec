# Solicitudes de reserva

## Purpose

Definir la creación de una petición de reserva vinculada a un solicitante, espacio e intervalo.

## ADDED Requirements

### Requirement: Crear solicitud válida
El sistema DEBE (SHALL) permitir que estudiantes y docentes autenticados creen una solicitud para sí mismos en un espacio activo, con fechas ISO 8601 que incluyan desplazamiento horario y un intervalo válido con `inicio < fin` y `inicio > ahora`. La solicitud se crea con estado `PENDIENTE` solo si no se solapa con una reserva aprobada del mismo espacio ni con otra solicitud pendiente solapada del mismo solicitante y espacio.

#### Scenario: Solicitud válida
- WHEN un estudiante o docente solicita un espacio activo con inicio futuro y fin posterior al inicio
- THEN el sistema guarda la solicitud como `PENDIENTE`, vinculada al actor autenticado

#### Scenario: Fin igual o anterior al inicio
- WHEN el intervalo solicitado tiene fin igual o anterior al inicio
- THEN el sistema rechaza la solicitud con error de validación y no crea reserva

#### Scenario: Fecha de inicio pasada
- WHEN el inicio solicitado es anterior al momento actual
- THEN el sistema rechaza la solicitud y explica que el inicio debe ser futuro

#### Scenario: Fecha de inicio igual al momento actual
- WHEN el inicio solicitado es igual al momento en que el sistema recibe la solicitud
- THEN el sistema rechaza la solicitud porque el inicio debe ser estrictamente futuro

#### Scenario: Fecha sin desplazamiento horario
- WHEN el inicio o el fin se envía sin zona/desplazamiento horario
- THEN el sistema rechaza los datos ambiguos y no crea reserva

#### Scenario: Solicitud para espacio inactivo
- WHEN un estudiante o docente solicita un espacio inactivo
- THEN el sistema rechaza la solicitud y explica que el espacio no está reservable

#### Scenario: Solicitud se solapa con reserva aprobada
- WHEN un estudiante o docente solicita un intervalo que se solapa con una reserva `APROBADA` del mismo espacio
- THEN el sistema rechaza la creación con un error de conflicto y no crea una solicitud pendiente

#### Scenario: Solicitud propia pendiente duplicada
- WHEN un solicitante intenta crear un intervalo que se solapa con otra solicitud `PENDIENTE` propia del mismo espacio
- THEN el sistema rechaza la creación como duplicado y conserva la solicitud existente

#### Scenario: Solicitudes pendientes solapadas de personas distintas
- WHEN dos solicitantes distintos crean intervalos solapados para el mismo espacio y no hay reserva aprobada que los bloquee
- THEN el sistema puede guardar ambas solicitudes como `PENDIENTE` y la aprobación deberá resolver el conflicto

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

### Requirement: Evitar duplicados propios concurrentes
El sistema DEBE (SHALL) comprobar solicitudes propias pendientes solapadas e insertar la nueva solicitud en una operación atómica, de modo que dos solicitudes simultáneas del mismo usuario y espacio no puedan eludir la regla de duplicados.

#### Scenario: Dos solicitudes propias concurrentes
- WHEN dos peticiones simultáneas del mismo usuario intentan crear intervalos solapados para el mismo espacio
- THEN como máximo una se guarda como `PENDIENTE` y la otra recibe un conflicto por duplicado
