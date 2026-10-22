# Diseño: capacidades iniciales de reservas

## Contexto y alcance

Este change define el contrato inicial de ocho capacidades para una API universitaria. Se limita a comportamiento verificable y no prescribe detalles de implementación que aún no se hayan probado.

## Decisiones

1. **Roles iniciales:** `ESTUDIANTE`, `DOCENTE`, `ADMIN_ESPACIOS` y `ADMIN_SISTEMA`. Un estudiante puede autorregistrarse y recibe solo `ESTUDIANTE`; asignar otros roles requiere acción del administrador del sistema. Un usuario con varios roles recibe la unión de sus permisos, siempre limitada por el ámbito de cada rol. El rol `ADMIN_ESPACIOS` solo gestiona/decide reservas de espacios asignados. El rol `ADMIN_SISTEMA` por sí solo no concede permisos de negocio.
2. **Estados:** `PENDIENTE`, `APROBADA`, `RECHAZADA` y `CANCELADA`. Solo una reserva `APROBADA` bloquea disponibilidad. Varias solicitudes pendientes pueden coincidir; cada intento de aprobación revalida conflictos y solo uno de dos intervalos incompatibles puede quedar aprobado.
   - Distintos solicitantes pueden mantener solicitudes pendientes solapadas. Un mismo solicitante no puede mantener dos solicitudes `PENDIENTE` con intervalos solapados para el mismo espacio; crear el duplicado se rechaza.
   - Una solicitud nueva se rechaza si ya se solapa con una reserva `APROBADA` del mismo espacio. La aprobación vuelve a validar para cubrir la carrera entre creación y decisión.
3. **Intervalos:** entrada ISO 8601 con desplazamiento horario obligatorio, normalizada a UTC para comparar. Los intervalos son semiabiertos `[inicio, fin)`. Se requiere `inicio < fin` y `inicio > ahora`; el inicio igual al momento de recepción ya no es futuro y se rechaza. No se define una zona civil institucional ni un horizonte máximo.
4. **Solapamiento:** para el mismo espacio hay conflicto si `nuevo_inicio < existente_fin AND existente_inicio < nuevo_fin`. La comprobación de duplicados propios y la inserción de solicitud, así como la comprobación de conflicto y aprobación, deben ser atómicas. La elección del bloqueo/aislamiento de SQLite y la estrategia de PostgreSQL quedan para diseño e implementación, con pruebas de concurrencia para ambas operaciones.
5. **Espacios e historial:** desactivar un espacio conserva referencias, solicitudes y auditoría y no cambia el estado de reservas ya existentes. El borrado físico solo se permite si no hay registros de solicitud/reserva relacionados; de lo contrario, se rechaza y se usa desactivación.
6. **Cancelación:** el solicitante puede cancelar sus solicitudes `PENDIENTE` o `APROBADA` sin plazo límite. El administrador de espacios asignado puede forzar la cancelación de esos estados solo con motivo obligatorio. La cancelación por `ADMIN_SISTEMA` sin rol de espacios se deniega.
7. **Errores:** se devuelven errores de validación, autenticación, autorización, inexistencia o conflicto con mensaje claro y sin exponer hashes/token/secretos. No se congela aquí un esquema HTTP de error específico.

## Matriz inicial de permisos

`Sí, ámbito propio/asignado` limita cada operación al usuario o espacio correspondiente. Un administrador del sistema no recibe permisos de negocio por defecto.

| Acción | ESTUDIANTE | DOCENTE | ADMIN_ESPACIOS | ADMIN_SISTEMA |
|---|---|---|---|---|
| Autorregistrarse como estudiante | Sí | No | No | No |
| Consultar catálogo/disponibilidad | Sí | Sí | Sí | Sí |
| Crear solicitud propia | Sí | Sí | No por el rol administrativo | No por el rol técnico |
| Consultar/cancelar solicitudes propias | Sí, propias | Sí, propias | Sí, propias | Sí, propias |
| Crear/actualizar/desactivar/eliminar espacio sin solicitudes | No | No | Sí, espacios asignados | No por el rol ADMIN_SISTEMA |
| Aprobar/rechazar solicitud | No | No | Sí, espacio asignado | No por el rol ADMIN_SISTEMA |
| Forzar cancelación de solicitud | No | No | Sí, espacio asignado y motivo obligatorio | No por el rol ADMIN_SISTEMA |
| Administrar cuentas y asignar roles | No | No | No | Sí |
| Consultar historial | Sí, propio | Sí, propio | Sí, espacios asignados | No por el rol ADMIN_SISTEMA |

La matriz se convertirá en pruebas positivas y negativas por rol. El administrador del sistema puede asignar roles y asignar administradores a espacios. El rol `ADMIN_SISTEMA` no tiene permisos de catálogo, decisión de reservas ni auditoría de negocio; para ello el usuario debe tener además el rol correspondiente.

Los permisos de varios roles se combinan por unión. No existen permisos individuales que anulen o amplíen la matriz: cualquier privilegio adicional requiere asignar el rol correspondiente y queda sujeto a su ámbito.

## Alternativas consideradas

- Bloquear disponibilidad a todos por cualquier solicitud pendiente: descartado porque una solicitud pendiente todavía no ha sido aprobada. Se permite que distintos solicitantes pidan una misma franja, pero se rechaza que un mismo solicitante genere otra solicitud pendiente solapada en el mismo espacio. La creación también detecta reservas aprobadas ya existentes; la aprobación vuelve a validar para cubrir la carrera entre creación y decisión.
- Intervalos cerrados: descartados porque harían colisionar reservas contiguas. El intervalo semiabierto permite adyacencia.
- Permitir a `ADMIN_SISTEMA` aprobar por defecto: descartado porque el plan separa administración técnica de decisiones de espacios.
- Eliminar físicamente espacios que ya tienen historial: descartado por pérdida de integridad y auditoría; se desactivan.

## Riesgos y validación

La atomicidad real depende del motor y del aislamiento. Se exigirá una prueba concurrente y se documentará el límite operativo de SQLite antes de implementar. La matriz detallada de permisos y la coherencia de estados se revisarán en `openspec/REVISION_SPECS.md` antes de programar.
