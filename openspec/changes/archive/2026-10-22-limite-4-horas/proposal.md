# Propuesta: limitar reservas consecutivas a cuatro horas

## Why

La institución establece que ninguna persona debe ocupar un espacio académico durante más de cuatro horas consecutivas. La regla necesita aplicarse al recibir solicitudes, para evitar reservas extensas y cadenas de reservas contiguas que superen el límite.

## What Changes

- Se añadirá una duración máxima de cuatro horas a la capacidad `solicitudes-reserva`.
- Se acumularán intervalos adyacentes de la misma persona y el mismo espacio que estén `PENDIENTE` o `APROBADA`; `RECHAZADA` y `CANCELADA` no cuentan.
- Cuatro horas exactas están permitidas. Se rechaza una duración individual o una cadena contigua cuya duración total supere cuatro horas.
- La regla aplica a solicitantes y excluye cuentas con `ADMIN_ESPACIOS` o `ADMIN_SISTEMA`, incluso si también tienen rol solicitante.
- El sistema devuelve un mensaje claro cuando la duración individual o acumulada supera el límite.

## Impacto previsto

| Área | Impacto esperado |
|---|---|
| Especificaciones | Modificar `solicitudes-reserva`. Las demás capacidades conservan estados y reglas; cancelaciones/rechazos ya no cuentan para la duración. |
| Código | Añadir validación en el servicio de reservas antes de insertar la solicitud, dentro de la transacción que serializa duplicados propios. |
| Pruebas | Cubrir cuatro horas exactas, cuatro horas y un minuto, cadena contigua excesiva, mismo usuario en distintos espacios, otro usuario, estados que cuentan y cuentas administradoras. |
| Datos existentes | No se alteran reservas ni estados previos. Solicitudes `PENDIENTE` y reservas `APROBADA` existentes pueden formar cadena con una nueva petición. No se requiere migración de esquema. |
| Plan de ingeniería | La sección de supuestos y estrategia temporal aún declaraba el límite como pendiente; el plan se actualizó en un commit separado anterior al delta de spec. |

## Decisiones de política aprobadas

1. Cuatro horas exactas se permiten; solo se rechaza una duración mayor.
2. La continuidad se acumula por misma persona y mismo espacio, contando `PENDIENTE` y `APROBADA`. `RECHAZADA` y `CANCELADA` no cuentan. Espacios o personas diferentes se evalúan por separado.
3. Se excluyen administradores. **Supuesto explícito:** una cuenta con rol `ADMIN_ESPACIOS` o `ADMIN_SISTEMA` está exenta aunque también tenga rol solicitante.

El responsable técnico respondió estas decisiones el 2026-10-22.
