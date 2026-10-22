# gestion-espacios Specification

## Purpose
Definir el catálogo central de espacios académicos y su disponibilidad administrativa.

## Requirements

### Requirement: Administrar espacios
El sistema DEBE (SHALL) permitir al administrador de espacios crear, consultar, actualizar y desactivar espacios con tipo, capacidad, ubicación y estado activo/inactivo, limitando la mutación a espacios asignados. Solo se permite eliminar físicamente un espacio sin solicitudes/reservas relacionadas. El rol `ADMIN_SISTEMA` por sí solo no muta espacios.

#### Scenario: Crear un espacio con datos válidos
- WHEN un usuario autorizado crea un espacio con tipo, capacidad positiva y ubicación válidos
- THEN el sistema guarda el espacio activo y devuelve sus datos identificables

#### Scenario: Rechazar capacidad no válida
- WHEN un usuario autorizado crea o actualiza un espacio con capacidad cero o negativa, o faltan tipo o ubicación
- THEN el sistema rechaza la operación con un error de validación claro y no cambia el catálogo

#### Scenario: Denegar gestión a un solicitante
- WHEN un estudiante o docente intenta crear, actualizar o desactivar un espacio
- THEN el sistema deniega la acción y conserva el estado previo

#### Scenario: Consultar espacio inactivo
- WHEN un usuario autenticado consulta el catálogo que incluye un espacio inactivo
- THEN el sistema informa su estado y no lo presenta como reservable

### Requirement: Preservar integridad del espacio
El sistema DEBE (SHALL) impedir el borrado físico de un espacio relacionado con una reserva; el operador autorizado DEBE desactivarlo para conservar referencias e historial.

#### Scenario: Borrar espacio sin solicitudes ni reservas
- WHEN un administrador de espacios asignado elimina un espacio sin solicitudes ni reservas relacionadas
- THEN el sistema elimina el registro y confirma la operación

#### Scenario: Borrar espacio con historial
- WHEN un administrador de espacios asignado solicita borrado físico de un espacio con cualquier solicitud o reserva relacionada
- THEN el sistema rechaza la operación, conserva el historial y permite desactivar el espacio

#### Scenario: Administrador del sistema muta el catálogo
- WHEN un usuario con solo el rol `ADMIN_SISTEMA` intenta crear, actualizar, desactivar o eliminar un espacio
- THEN el sistema deniega la acción
