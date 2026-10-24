# interfaz-web Specification

## Purpose
Permitir que los actores utilicen desde un navegador los casos de uso del sistema de reservas, conservando la API como autoridad para validación y autorización.

## Requirements

### Requirement: Servir la interfaz de la aplicación
La aplicación DEBE (SHALL) mostrar la interfaz web en español en la ruta raíz `/` y mantener disponible la documentación OpenAPI en `/docs`. La interfaz DEBE (SHALL) servirse desde el mismo origen que la API y no requerir un proceso de compilación frontend separado.

#### Scenario: Abrir la aplicación
- WHEN una persona abre `GET /`
- THEN el servidor devuelve la página inicial de la aplicación y no un error `404` o `405`

#### Scenario: Abrir la documentación técnica
- WHEN una persona abre `GET /docs`
- THEN el servidor presenta la documentación interactiva de la API

### Requirement: Registrar, iniciar y cerrar sesión desde la interfaz
La interfaz DEBE (SHALL) permitir el registro de estudiantes y el inicio de sesión mediante formularios que consumen los endpoints existentes. La interfaz DEBE (SHALL) presentar errores comprensibles y no almacenar ni mostrar la contraseña después de enviar el formulario. Al cerrar sesión, DEBE (SHALL) eliminar el token de la sesión visual.

#### Scenario: Registro válido
- WHEN una persona envía desde la interfaz un correo nuevo y una contraseña válida
- THEN la interfaz envía el registro al backend, informa que la cuenta de estudiante fue creada y permite iniciar sesión

#### Scenario: Inicio de sesión válido
- WHEN una cuenta activa envía credenciales válidas
- THEN la interfaz obtiene el token, muestra la aplicación autenticada y presenta el rol devuelto por el servidor

#### Scenario: Credenciales incorrectas
- WHEN una persona envía credenciales inválidas
- THEN la interfaz muestra un error comprensible y no crea una sesión autenticada

#### Scenario: Cerrar sesión
- WHEN una persona autenticada selecciona cerrar sesión
- THEN la interfaz elimina el token de sesión y vuelve a la pantalla de acceso

### Requirement: Consumir la API y respetar la autorización del servidor
La interfaz DEBE (SHALL) enviar el token de sesión en las solicitudes protegidas y DEBE (SHALL) representar los permisos devueltos por el backend como ayudas de navegación. Ocultar una acción en la interfaz NO DEBE sustituir la autorización del servidor. Ante `401` la interfaz DEBE (SHALL) finalizar la sesión visual; ante `403`, `409` o errores de validación, DEBE (SHALL) mostrar el mensaje de error sin indicar que la operación tuvo éxito.

#### Scenario: Sesión ausente
- WHEN una persona intenta una operación protegida sin token válido
- THEN el backend deniega la operación y la interfaz solicita autenticación

#### Scenario: Permiso insuficiente
- WHEN una persona intenta una operación que su rol no permite
- THEN la API devuelve denegación y la interfaz informa que no tiene permiso, sin modificar datos

#### Scenario: Error de conflicto o validación
- WHEN una operación falla por datos inválidos, conflicto de horario o estado no permitido
- THEN la interfaz muestra el error recibido y conserva visible el formulario para corregirlo cuando sea posible

### Requirement: Consultar espacios y disponibilidad
La interfaz DEBE (SHALL) permitir consultar los espacios activos y solicitar disponibilidad para un espacio e intervalo con zona horaria explícita. Debe distinguir espacio no disponible, espacio inactivo e intervalo inválido mediante los resultados de la API.

#### Scenario: Consultar disponibilidad
- WHEN una persona autenticada selecciona un espacio activo y un intervalo válido
- THEN la interfaz presenta el resultado de disponibilidad de la API para ese espacio e intervalo

#### Scenario: Intervalo inválido
- WHEN una persona consulta un intervalo con fin igual o anterior al inicio o sin desplazamiento horario
- THEN la interfaz muestra el error de validación y no presenta el intervalo como disponible

### Requirement: Crear y consultar solicitudes propias
La interfaz DEBE (SHALL) permitir a estudiantes y docentes crear solicitudes y consultar sus solicitudes e historial usando los endpoints existentes. Debe mostrar el estado de cada solicitud, el espacio y las fechas con desplazamiento horario comprensible.

#### Scenario: Crear solicitud válida
- WHEN un estudiante o docente autenticado envía una solicitud válida para un espacio e intervalo disponible
- THEN la interfaz presenta la solicitud creada con estado `PENDIENTE`

#### Scenario: Solicitud rechazada por regla de negocio
- WHEN el backend rechaza una solicitud por espacio inactivo, solapamiento, duplicado propio o más de cuatro horas consecutivas
- THEN la interfaz informa la causa devuelta y no muestra la solicitud como creada

#### Scenario: Consultar solicitudes e historial
- WHEN una persona autenticada abre sus solicitudes o el historial de una de ellas
- THEN la interfaz muestra únicamente los datos que autoriza el backend y las entradas de auditoría disponibles

### Requirement: Cancelar una solicitud permitida
La interfaz DEBE (SHALL) ofrecer la acción de cancelación cuando resulte pertinente y enviar la solicitud al endpoint existente. El backend seguirá decidiendo si el actor, estado y motivo permiten cancelar.

#### Scenario: Cancelación permitida
- WHEN el solicitante cancela una solicitud en un estado cancelable y confirma la acción
- THEN la interfaz muestra el estado actualizado devuelto por la API

#### Scenario: Cancelación denegada
- WHEN el backend deniega una cancelación por permiso o estado
- THEN la interfaz informa el error y conserva el estado real de la solicitud

### Requirement: Administrar espacios y decisiones de reservas
La interfaz DEBE (SHALL) ofrecer herramientas de gestión de espacios a cuentas con permisos de administrador de espacios y herramientas de cuentas/roles a cuentas con permisos de administrador del sistema. Los administradores de espacios DEBEN (SHALL) poder revisar solicitudes de sus espacios y, cuando la API lo autorice, aprobarlas o rechazarlas con motivo. Toda operación administrativa DEBE (SHALL) enviarse al backend para validación.

#### Scenario: Administrador de espacios gestiona un espacio
- WHEN una cuenta autorizada consulta o modifica un espacio dentro de su ámbito
- THEN la interfaz presenta y actualiza el resultado de la API

#### Scenario: Administrador de espacios decide una solicitud
- WHEN un administrador asignado aprueba una solicitud compatible o rechaza una solicitud proporcionando motivo
- THEN la interfaz presenta el estado final y el resultado auditado devuelto por la API

#### Scenario: Solicitante intenta una operación administrativa
- WHEN un estudiante o docente intenta ejecutar una operación administrativa desde la interfaz o directamente desde la API
- THEN el backend deniega la operación y la interfaz no presenta un resultado exitoso

#### Scenario: Administrador del sistema administra cuentas
- WHEN un administrador del sistema consulta cuentas o asigna un rol permitido
- THEN la interfaz presenta la operación autorizada y los datos públicos devueltos por la API

### Requirement: Mantener una interfaz utilizable y accesible
La interfaz DEBE (SHALL) etiquetar los controles de formulario, permitir navegación por teclado, mostrar estados de carga y proporcionar mensajes de éxito o error perceptibles sin depender únicamente del color. La interfaz DEBE (SHALL) adaptarse a anchos de escritorio y móvil sin perder acceso a las funciones disponibles.

#### Scenario: Navegación por teclado
- WHEN una persona usa únicamente teclado para recorrer un formulario
- THEN puede identificar el foco, completar controles y activar la acción principal

#### Scenario: Ancho móvil
- WHEN una persona abre la aplicación en una pantalla estrecha
- THEN el contenido principal y sus acciones siguen visibles y utilizables sin desplazamiento horizontal de la página
