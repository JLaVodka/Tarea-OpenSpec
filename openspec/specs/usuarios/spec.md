# usuarios Specification

## Purpose
Definir el alta de cuentas, su administración segura y la autenticación para consumir la API.

## Requirements

### Requirement: Registrar estudiantes
El sistema DEBE (SHALL) permitir autorregistro de una cuenta de estudiante con credenciales válidas y asignar únicamente el rol `ESTUDIANTE`. El correo se normaliza quitando espacios externos y comparando sin distinguir mayúsculas. La persona solicitante no puede asignarse ni elevar su propio rol.

#### Scenario: Autorregistro válido
- WHEN una persona se registra con datos requeridos válidos y una dirección de correo no utilizada
- THEN el sistema crea una cuenta activa con rol `ESTUDIANTE` y no concede otros roles

#### Scenario: Correo duplicado
- WHEN una persona intenta registrarse con una dirección que, tras normalizarse, pertenece a otra cuenta
- THEN el sistema rechaza el registro con un error claro y no crea una segunda cuenta

#### Scenario: Intento de elegir rol privilegiado
- WHEN el registro solicita un rol `DOCENTE`, `ADMIN_ESPACIOS` o `ADMIN_SISTEMA`
- THEN el sistema ignora/rechaza la asignación solicitada y no crea una cuenta con privilegios elevados

### Requirement: Administrar cuentas
El sistema DEBE (SHALL) permitir al administrador del sistema consultar y gestionar el estado de cuentas, asignar roles no disponibles en autorregistro y asignar administradores de espacios a los espacios que gestionarán. Ningún usuario puede elevar sus propios permisos.

#### Scenario: Asignar rol autorizado
- WHEN un administrador del sistema asigna el rol `DOCENTE` a una cuenta existente
- THEN el sistema registra la asignación y la atribuye al actor administrativo

#### Scenario: Asignar administrador a un espacio
- WHEN un administrador del sistema asigna a una cuenta con rol `ADMIN_ESPACIOS` la gestión de un espacio
- THEN el sistema registra la asignación de ámbito y la atribuye al actor administrativo

#### Scenario: Intentar elevar el propio rol
- WHEN un administrador del sistema intenta asignarse a sí mismo un rol o ámbito que no tenía
- THEN el sistema deniega la operación y conserva las asignaciones anteriores

#### Scenario: Solicitante intenta administrar cuentas
- WHEN un estudiante o docente intenta consultar información administrativa, cambiar estado o asignar roles de otra cuenta
- THEN el sistema deniega la operación

#### Scenario: Administrador de espacios intenta asignar roles
- WHEN un administrador de espacios intenta asignar roles o cambiar el estado de una cuenta
- THEN el sistema deniega la operación salvo permiso administrativo explícito

### Requirement: Autenticar sin exponer secretos
El sistema DEBE (SHALL) verificar credenciales contra un hash de contraseña seguro y emitir un JWT válido solo para una cuenta activa. Nunca DEBE devolver contraseñas, hashes ni secretos del token en respuestas.

#### Scenario: Inicio de sesión válido
- WHEN una cuenta activa envía credenciales correctas
- THEN el sistema devuelve un token de autenticación y los datos públicos permitidos de la cuenta

#### Scenario: Credenciales incorrectas o cuenta desactivada
- WHEN una persona inicia sesión con contraseña incorrecta, cuenta inexistente o cuenta desactivada
- THEN el sistema rechaza la autenticación con un error que no revela cuál condición ocurrió

#### Scenario: Token inválido o expirado
- WHEN una solicitud protegida presenta un token inválido, malformado o expirado
- THEN el sistema rechaza el acceso sin revelar secretos y no ejecuta la acción solicitada
