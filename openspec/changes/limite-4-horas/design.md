# Diseño: límite de cuatro horas consecutivas

## Decisiones aprobadas

- **Inclusividad:** cuatro horas exactas se permiten; una duración mayor se rechaza.
- **Agrupación de continuidad:** sumar intervalos adyacentes de la misma persona en el mismo espacio. Cuentan reservas `PENDIENTE` y `APROBADA`; no cuentan `RECHAZADA` ni `CANCELADA`. Espacios diferentes y personas diferentes se evalúan por separado.
- **Roles:** la regla aplica a cuentas solicitantes. Se excluye una cuenta si tiene `ADMIN_ESPACIOS` o `ADMIN_SISTEMA`, aunque tenga además un rol solicitante. Esta interpretación explícita resuelve el caso de roles combinados.
- **Datos previos:** no se modifica ningún registro existente. Las reservas `PENDIENTE` y `APROBADA` previas pueden formar una cadena con una nueva solicitud y hacer que esta se rechace; las rechazadas y canceladas no afectan el cómputo. No se requiere cambio de esquema.

## Decisión técnica

La validación individual y la suma de intervalos adyacentes se ejecutarán dentro de la misma sección crítica transaccional que detecta duplicados propios. Se consultarán registros `PENDIENTE` y `APROBADA` del mismo solicitante y espacio; al agregar el nuevo intervalo, se calculará la extensión temporal de su cadena contigua. Una cadena con duración total de hasta cuatro horas se permite. Si supera cuatro horas, se rechaza con un mensaje que identifica el límite. La operación conserva la serialización SQLite (`BEGIN IMMEDIATE`) y PostgreSQL (bloqueo de fila del espacio).

## Impacto

La spec modificada es `solicitudes-reserva`. No cambian entidades, columnas ni estados, por lo que no se requiere migración. La prueba concurrente debe demostrar que dos solicitudes adyacentes propias que juntas excederían cuatro horas no pueden persistirse ambas. Los escenarios requieren cuatro horas exactas permitidas, cuatro horas y un minuto rechazadas, continuidad excesiva, distintos espacios, otros usuarios, error claro y exención administrativa.

## Alternativas descartadas

- Validar solo la duración de cada solicitud: descartado porque una persona podría superar el límite mediante varias solicitudes contiguas.
- Sumar solicitudes de espacios diferentes o de usuarios diferentes: descartado porque la regla limita la ocupación consecutiva del mismo espacio por una persona.
- Contar solicitudes rechazadas o canceladas: descartado porque dejaron de representar tiempo reservado.
