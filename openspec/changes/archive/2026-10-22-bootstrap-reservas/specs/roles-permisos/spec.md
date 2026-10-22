# Roles y permisos

## Purpose

Definir la autorización por roles para separar solicitud, administración de espacios y administración técnica.

## ADDED Requirements

### Requirement: Autorizar operaciones de solicitantes
El sistema DEBE (SHALL) permitir a `ESTUDIANTE` y `DOCENTE` autenticados consultar el catálogo/disponibilidad y crear, consultar o cancelar sus propias solicitudes. Estos roles no administran espacios ni deciden solicitudes.

#### Scenario: Estudiante solicita una reserva propia
- WHEN un estudiante autenticado crea una solicitud para sí mismo
- THEN el sistema autoriza la acción si los datos son válidos

#### Scenario: Docente solicita una reserva propia
- WHEN un docente autenticado crea una solicitud para sí mismo
- THEN el sistema autoriza la acción si los datos son válidos

#### Scenario: Solicitante accede a solicitud ajena
- WHEN un estudiante o docente consulta o cancela una solicitud de otra persona
- THEN el sistema deniega la acción sin modificar ni revelar la solicitud

### Requirement: Limitar administración al ámbito de espacios
El sistema DEBE (SHALL) permitir a `ADMIN_ESPACIOS` administrar espacios asignados, revisar solicitudes de esos espacios, decidirlas y consultar su historial; no debe autorizar operaciones fuera de ese ámbito.

#### Scenario: Administrador de espacios gestiona un espacio asignado
- WHEN un administrador de espacios ejecuta una acción de catálogo o decisión sobre un espacio asignado
- THEN el sistema autoriza solo las acciones permitidas por la matriz

#### Scenario: Administrador de espacios accede a espacio no asignado
- WHEN un administrador de espacios administra o decide una solicitud de un espacio no asignado
- THEN el sistema deniega la acción

### Requirement: Limitar el rol de administrador del sistema
El sistema DEBE (SHALL) permitir a `ADMIN_SISTEMA` administrar cuentas, asignar roles y asignar espacios a administradores. Este rol por sí solo no concede permisos de negocio sobre reservas o catálogo.

#### Scenario: Administrador del sistema intenta aprobar una reserva
- WHEN un usuario con solo el rol `ADMIN_SISTEMA` intenta aprobar o rechazar una solicitud
- THEN el sistema deniega la acción

#### Scenario: Administrador del sistema asigna un ámbito
- WHEN un usuario con rol `ADMIN_SISTEMA` asigna un espacio a un usuario con rol `ADMIN_ESPACIOS`
- THEN el sistema registra el ámbito y permite al administrador actuar solo en ese espacio

### Requirement: Combinar roles y denegar por defecto
El sistema DEBE (SHALL) combinar por unión los permisos de los roles asignados, respetar el ámbito de cada rol y denegar cualquier acción sin permiso explícito en la matriz. No existen permisos directos por usuario que amplíen la matriz.

#### Scenario: Usuario con roles combinados
- WHEN una cuenta tiene `ADMIN_SISTEMA` y `ADMIN_ESPACIOS` y actúa sobre un espacio asignado
- THEN el sistema autoriza únicamente las acciones de `ADMIN_ESPACIOS` dentro de ese ámbito

#### Scenario: Falta autenticación
- WHEN una solicitud sin credenciales invoca una acción protegida
- THEN el sistema deniega el acceso y no revela datos del recurso

#### Scenario: Rol sin permiso
- WHEN un usuario autenticado intenta una acción fuera de los permisos de sus roles
- THEN el sistema deniega la acción sin modificar datos
