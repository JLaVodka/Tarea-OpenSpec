# solicitudes-reserva Specification

## Purpose
Definir la creación de una petición de reserva vinculada a un solicitante, espacio e intervalo.

## Requirements

### Requirement: Crear solicitud válida
El sistema DEBE (SHALL) permitir que estudiantes y docentes autenticados creen para sí una solicitud `PENDIENTE` en un espacio activo, con fechas ISO 8601 con desplazamiento horario, `inicio < fin` e `inicio > ahora`. El sistema no DEBE crear la solicitud si se solapa con una reserva `APROBADA` del espacio o una solicitud `PENDIENTE` solapada del mismo solicitante y espacio.

#### Scenario: Solicitud válida
- WHEN un estudiante o docente solicita un espacio activo con inicio futuro, fin posterior al inicio y duración permitida
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

### Requirement: Limitar reservas consecutivas a cuatro horas
El sistema DEBE (SHALL) limitar a cuatro horas inclusive la cadena contigua activa de una persona sin rol administrativo para un mismo espacio. Para el cómputo cuentan `PENDIENTE` y `APROBADA`; se excluyen `RECHAZADA` y `CANCELADA`. Una cuenta con rol `ADMIN_ESPACIOS` o `ADMIN_SISTEMA` está exenta.

#### Scenario: Permitir exactamente cuatro horas
- WHEN un solicitante sin rol administrativo crea una solicitud de exactamente cuatro horas sin extender una cadena activa más allá del límite
- THEN el sistema guarda la solicitud `PENDIENTE`

#### Scenario: Rechazar cuatro horas y un minuto
- WHEN un solicitante sin rol administrativo crea una solicitud individual de cuatro horas y un minuto
- THEN el sistema rechaza la solicitud, informa que el máximo es cuatro horas y no crea un registro

#### Scenario: Rechazar una cadena contigua que supera cuatro horas
- WHEN una persona tiene un intervalo `PENDIENTE` o `APROBADA` de tres horas y solicita inmediatamente después otro intervalo de dos horas para el mismo espacio
- THEN el sistema rechaza la nueva solicitud con un mensaje claro del límite de cuatro horas

#### Scenario: Solicitudes contiguas de una persona en espacios distintos
- WHEN una persona solicita intervalos contiguos que superan cuatro horas en total, pero corresponden a espacios distintos
- THEN el sistema evalúa cada espacio por separado y permite la nueva solicitud si no viola otra regla

#### Scenario: Intervalos contiguos de personas distintas
- WHEN otra persona solicita un intervalo contiguo en el mismo espacio y la duración excedería cuatro horas solo al sumar ambas personas
- THEN el sistema calcula el límite únicamente para la nueva persona y permite la solicitud si no viola otra regla

#### Scenario: Una solicitud cancelada o rechazada no suma al límite
- WHEN la única solicitud contigua de la persona está `RECHAZADA` o `CANCELADA`
- THEN el sistema no la cuenta y evalúa la nueva solicitud con los intervalos activos restantes

#### Scenario: Eximir cuentas con rol administrativo
- WHEN una cuenta con `ADMIN_ESPACIOS` o `ADMIN_SISTEMA` y rol solicitante crea una solicitud propia de más de cuatro horas
- THEN el sistema no aplica el límite de duración de cuatro horas a esa cuenta

### Requirement: Comprobar el límite consecutivo atómicamente
El sistema DEBE (SHALL) comprobar el máximo de cuatro horas consecutivas e insertar la nueva solicitud en una operación atómica, de modo que peticiones simultáneas no puedan eludir el límite por continuidad.

#### Scenario: Dos solicitudes contiguas concurrentes superan el límite
- WHEN dos peticiones simultáneas contiguas de la misma persona y el mismo espacio, que individualmente cumplen cuatro horas, juntas superan cuatro horas
- THEN como máximo se guarda una solicitud y la otra recibe un conflicto claro por el límite consecutivo
