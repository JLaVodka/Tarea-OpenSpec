# Roles y permisos

## Purpose

Definir la autorización por roles para separar solicitud, administración de espacios y administración técnica.

## ADDED Requirements

### Requirement: Aplicar la matriz de permisos
El sistema DEBE (SHALL) comprobar el permiso requerido para cada acción protegida. Los roles iniciales son `ESTUDIANTE`, `DOCENTE`, `ADMIN_ESPACIOS` y `ADMIN_SISTEMA`; una ruta protegida no se autoriza solo por tener un usuario autenticado.

#### Scenario: Estudiante solicita una reserva propia
- WHEN un estudiante autenticado crea una solicitud para sí mismo
- THEN el sistema autoriza la acción si los datos de la solicitud son válidos

#### Scenario: Docente solicita una reserva propia
- WHEN un docente autenticado crea una solicitud para sí mismo
- THEN el sistema autoriza la acción si los datos de la solicitud son válidos

#### Scenario: Administrador de espacios administra un espacio asignado
- WHEN un administrador de espacios ejecuta una acción sobre un espacio asignado a ese administrador
- THEN el sistema autoriza únicamente las acciones de catálogo o decisión que su permiso permita

#### Scenario: Administrador de espacios accede a espacio no asignado
- WHEN un administrador de espacios administra o decide una solicitud de un espacio no asignado
- THEN el sistema deniega la acción

#### Scenario: Administrador del sistema intenta aprobar una reserva
- WHEN un administrador del sistema intenta aprobar o rechazar una solicitud sin el permiso explícito `reservas:decidir`
- THEN el sistema deniega la acción; el rol técnico no implica aprobación de negocio

### Requirement: Denegar por defecto y exigir autenticación
El sistema DEBE (SHALL) denegar por defecto una acción sin permiso explícito y exigir autenticación para consultar datos no públicos o ejecutar operaciones protegidas.

#### Scenario: Falta autenticación
- WHEN una solicitud sin credenciales invoca una acción protegida
- THEN el sistema rechaza el acceso y no revela datos del recurso

#### Scenario: Rol sin permiso
- WHEN un usuario autenticado intenta una acción que no está permitida a su rol
- THEN el sistema deniega la acción sin modificar datos

#### Scenario: Acceso permitido
- WHEN un usuario autenticado con el permiso requerido invoca la acción sobre un recurso dentro de su ámbito
- THEN el sistema permite la acción y aplica además las validaciones de negocio
