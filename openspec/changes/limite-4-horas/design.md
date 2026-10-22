# Diseño: límite de cuatro horas consecutivas

## Estado de decisiones

Este diseño está pendiente de las decisiones del responsable técnico. No hay deltas de especificación ni tareas de implementación hasta resolverlas.

## Opciones presentadas

- **Inclusividad:** permitir exactamente cuatro horas y rechazar duraciones superiores, o interpretar cuatro horas como límite exclusivo.
- **Agrupación de continuidad:** sumar reservas adyacentes de la misma persona en el mismo espacio o medir cada solicitud por separado. Debe definirse si cuentan solicitudes `PENDIENTE` además de reservas `APROBADA`; las reservas `RECHAZADA` y `CANCELADA` no deberían consumir tiempo reservado.
- **Alcance por rol:** aplicar la restricción a todo actor que solicita para sí mismo o limitarla a determinados roles.

## Impactos de implementación previstos

La comprobación debe ejecutarse en el servicio de reservas antes de persistir una nueva solicitud y formar parte de la misma sección crítica que evita duplicados propios. Las pruebas de frontera deben usar instantes UTC y verificar intervalos semiabiertos. Los datos existentes se conservan; el impacto sobre solicitudes ya creadas se limita a que puedan impedir o no una nueva solicitud contigua según los estados que se aprueben.

## Alternativas por decidir

La alternativa más simple sería limitar individualmente cada petición; no detectaría cadenas de solicitudes contiguas. La alternativa acumulativa por persona y espacio evita eludir el máximo mediante reservas adyacentes, pero requiere consultar las solicitudes activas del mismo intervalo temporal. La decisión corresponde al responsable técnico.
