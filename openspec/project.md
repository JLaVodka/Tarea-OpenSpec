# Contexto del proyecto

## Propósito

Sistema universitario para centralizar solicitudes y reservas de laboratorios, auditorios y salas de cómputo. Debe consultar disponibilidad, evitar conflictos de horarios, aplicar permisos y conservar evidencia de las decisiones.

## Alcance inicial

La prioridad es una API REST funcional y probada. Se incluyen usuarios y autenticación, roles/permisos, gestión de espacios, solicitudes, consulta de disponibilidad, prevención de solapamientos, aprobación/rechazo, cancelación e historial. La interfaz web completa, SSO, calendarios externos, notificaciones, recurrencias y despliegue productivo están fuera del alcance inicial.

## Arquitectura

Monolito modular en capas: routers HTTP, servicios de aplicación/reglas de negocio, repositorios y persistencia. Los módulos lógicos son usuarios, roles/permisos, espacios, reservas, disponibilidad y auditoría. Pydantic define contratos de API y SQLAlchemy encapsula el acceso relacional. Las reglas de negocio se aplican en servicios y no se delegan a los routers ni repositorios.

## Stack aprobado en el plan

- Python 3 y FastAPI para la API.
- SQLAlchemy 2 y Pydantic.
- SQLite para desarrollo/pruebas, con diseño portable a PostgreSQL.
- JWT y contraseñas con hash Argon2 o bcrypt.
- pytest, pytest-cov y httpx/TestClient.
- Creación controlada de esquema inicialmente; Alembic si la evolución requiere migraciones versionadas.

Las versiones de dependencias se fijarán al iniciar implementación. No introducir tecnologías o capas sin justificación y aprobación.

## Modelo preliminar

User puede tener varios Role; Role agrupa Permission. Space tiene muchas Reservation. Reservation identifica espacio, solicitante, intervalo, estado y fechas de transición. ReservationEvent relaciona una reserva con el actor, el tipo de evento, la fecha y el detalle pertinente. El modelo se refinará en las specs antes de programar.

## Convenciones de negocio y de especificación

- Escribir documentación en español; conservar los encabezados estructurales que exige OpenSpec y las palabras clave SHALL/MUST en inglés donde el validador las requiera. Los identificadores de código serán en inglés.
- Cada requisito debe ser verificable y normativo (DEBE/SHALL/MUST) y tener escenarios `#### Scenario:` con condiciones `WHEN` y resultados `THEN`.
- Especificar permisos y errores, además del camino feliz y casos límite.
- Usar intervalos semiabiertos `[inicio, fin)` como hipótesis para que reservas adyacentes no se solapen. La regla final de conflictos y qué estados bloquean una franja debe quedar explícita en las specs.
- Comprobar solapamiento del mismo espacio con `nuevo_inicio < existente_fin AND existente_inicio < nuevo_fin`. La validación y escritura deben ser atómicas y cubrir carreras; el mecanismo concreto se especificará antes de implementar.
- No inventar políticas institucionales. La duración máxima de cuatro horas consecutivas está aprobada y se define en `changes/limite-4-horas`; cuatro horas son inclusivas, la continuidad suma solicitudes pendientes y reservas aprobadas por persona/espacio, y se excluyen cuentas administradoras. Zona horaria institucional, anticipación, horarios hábiles y excepciones adicionales permanecen pendientes si no hay aprobación explícita.
- No implementar requisitos que no hayan pasado revisión y aprobación. Si falta un requisito, proponer primero un change OpenSpec.

## Flujo de trabajo

Respetar el orden: plan aprobado → contexto/specs OpenSpec → revisión de specs aprobada → implementación trazada → cambio de regla (spec antes que código) → cierre. Separar commits por etapa con Conventional Commits. Al terminar cada fase, presentar resumen y evidencia, y esperar aprobación explícita antes de continuar.

## Decisiones responsables

El estudiante es responsable de aprobar fases y decidir políticas de negocio, roles, excepciones, zona horaria, cancelaciones, cambios de stack y publicación. La IA puede redactar, proponer e implementar tareas aprobadas, pero no sustituye esas decisiones ni afirma pruebas sin ejecutarlas.
