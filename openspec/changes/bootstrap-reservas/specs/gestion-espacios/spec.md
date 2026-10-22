# Gestión de espacios

## Purpose

Definir el catálogo central de espacios académicos y su disponibilidad administrativa.

## ADDED Requirements

### Requirement: Administrar espacios
El sistema DEBE (SHALL) permitir al administrador de espacios crear, consultar, actualizar y desactivar espacios con tipo, capacidad, ubicación y estado activo/inactivo. El administrador del sistema puede administrar el catálogo según el permiso explícito `espacios:administrar`; otros roles no pueden mutarlo.

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

#### Scenario: Borrar espacio sin reservas
- WHEN un administrador autorizado elimina un espacio sin solicitudes ni reservas relacionadas
- THEN el sistema elimina el registro y confirma la operación

#### Scenario: Borrar espacio con historial
- WHEN un administrador autorizado solicita borrado físico de un espacio con reservas relacionadas
- THEN el sistema rechaza la operación, conserva el historial y permite desactivar el espacio
