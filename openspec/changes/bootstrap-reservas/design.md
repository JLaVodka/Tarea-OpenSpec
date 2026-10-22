# Diseño: capacidades iniciales de reservas

## Contexto y alcance

Este change define el contrato inicial de ocho capacidades para una API universitaria. Se limita a comportamiento verificable y no prescribe detalles de implementación que aún no se hayan probado.

## Decisiones

1. **Roles iniciales:** `ESTUDIANTE`, `DOCENTE`, `ADMIN_ESPACIOS` y `ADMIN_SISTEMA`. Un estudiante puede autorregistrarse y recibe solo `ESTUDIANTE`; asignar otros roles requiere acción del administrador del sistema. El administrador de espacios solo gestiona/decide reservas de espacios que tiene asignados. Ser administrador del sistema no concede implícitamente aprobación de reservas.
2. **Estados:** `PENDIENTE`, `APROBADA`, `RECHAZADA` y `CANCELADA`. Solo una reserva `APROBADA` bloquea disponibilidad. Varias solicitudes pendientes pueden coincidir; cada intento de aprobación revalida conflictos y solo uno de dos intervalos incompatibles puede quedar aprobado.
3. **Intervalos:** entrada ISO 8601 con desplazamiento horario obligatorio, normalizada a UTC para comparar. Los intervalos son semiabiertos `[inicio, fin)`. Se requiere `inicio < fin`; si `inicio` es anterior al momento actual la solicitud se rechaza. No se define una zona civil institucional ni un horizonte máximo.
4. **Solapamiento:** para el mismo espacio hay conflicto si `nuevo_inicio < existente_fin AND existente_inicio < nuevo_fin`. La validación y escritura deben ser atómicas. La elección del bloqueo/aislamiento de SQLite y la estrategia de PostgreSQL quedan para diseño e implementación, con prueba de concurrencia.
5. **Espacios e historial:** desactivar un espacio conserva referencias y auditoría. El borrado físico solo se permite si no existen reservas; con reservas relacionadas, se rechaza y se usa desactivación.
6. **Errores:** se devuelven errores de validación, autenticación, autorización, inexistencia o conflicto con mensaje claro y sin exponer hashes/token/secretos. No se congela aquí un esquema HTTP de error específico.

## Matriz inicial de permisos

`Sí, ámbito propio/asignado` limita cada operación al usuario o espacio correspondiente. Un administrador del sistema no recibe permisos de negocio por defecto.

| Acción | ESTUDIANTE | DOCENTE | ADMIN_ESPACIOS | ADMIN_SISTEMA |
|---|---|---|---|---|
| Autorregistrarse como estudiante | Sí | No | No | No |
| Consultar catálogo/disponibilidad | Sí | Sí | Sí | Sí |
| Crear solicitud propia | Sí | Sí | No por el rol administrativo | No por el rol técnico |
| Consultar/cancelar solicitudes propias | Sí, propias | Sí, propias | Sí, propias | Sí, propias |
| Crear/actualizar/desactivar espacio | No | No | Sí, espacios asignados | No por defecto; solo con permiso explícito |
| Aprobar/rechazar solicitud | No | No | Sí, espacio asignado | No por defecto; requiere `reservas:decidir` explícito |
| Administrar cuentas y asignar roles | No | No | No | Sí |
| Consultar historial | Sí, propio | Sí, propio | Sí, espacios asignados | No por defecto; requiere permiso explícito |

La matriz se convertirá en pruebas positivas y negativas por rol. Asignar roles y asignaciones de espacios será una operación administrativa auditada; los mecanismos concretos de gestión se especificarán con usuarios/permisos antes de implementación.

## Alternativas consideradas

- Bloquear una franja al crear cualquier solicitud: descartado porque una solicitud pendiente todavía no ha sido aprobada. Se revalida al aprobar para evitar sobreventa.
- Intervalos cerrados: descartados porque harían colisionar reservas contiguas. El intervalo semiabierto permite adyacencia.
- Permitir a `ADMIN_SISTEMA` aprobar por defecto: descartado porque el plan separa administración técnica de decisiones de espacios.
- Eliminar físicamente espacios que ya tienen historial: descartado por pérdida de integridad y auditoría; se desactivan.

## Riesgos y validación

La atomicidad real depende del motor y del aislamiento. Se exigirá una prueba concurrente y se documentará el límite operativo de SQLite antes de implementar. La matriz detallada de permisos y la coherencia de estados se revisarán en `openspec/REVISION_SPECS.md` antes de programar.
