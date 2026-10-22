# Propuesta: limitar reservas consecutivas a cuatro horas

## Por qué

La institución establece que ninguna persona debe ocupar un espacio académico durante más de cuatro horas consecutivas. La regla necesita aplicarse uniformemente al recibir solicitudes, para evitar reservas extensas y cadenas de reservas contiguas que superen el límite.

## Qué cambia

- Se añadirá una duración máxima de cuatro horas a la capacidad `solicitudes-reserva`.
- Se definirá cómo se agregan reservas contiguas de una misma persona y qué estados cuentan para el límite.
- Se mantendrán los intervalos semiabiertos y la interpretación aprobada de cuatro horas exactas como caso permitido, salvo decisión distinta del responsable técnico.
- El sistema devolverá un error claro cuando una solicitud exceda el límite por su duración o por continuidad con otra solicitud.

## Impacto previsto

| Área | Impacto esperado |
|---|---|
| Especificaciones | Modificar `solicitudes-reserva`; revisar consistencia con `disponibilidad`, `prevencion-reservas-simultaneas` y `cancelacion-historial` si los estados o la liberación de intervalos afectan el cómputo. |
| Código | Añadir validación en el servicio de reservas antes de insertar la solicitud; el esquema HTTP puede conservar las fechas actuales. |
| Pruebas | Cubrir cuatro horas exactas, cuatro horas y un minuto, cadena contigua que excede el límite, solicitante en distintos espacios y usuarios distintos. |
| Datos existentes | No se propone alterar reservas previas ni cambiar estados existentes. Las nuevas solicitudes se validarán contra los registros activos que determine la decisión aprobada. No se requiere migración de esquema prevista. |
| Plan de ingeniería | La sección de supuestos y estrategia temporal hoy deja duración máxima como decisión pendiente. Si se aprueba la regla, se actualizará el plan y su historial en un commit separado antes del delta de spec. |

## Dudas de política para aprobación

1. ¿Cuatro horas exactas se permiten y solo se rechaza una duración mayor?
2. ¿La continuidad se acumula únicamente para la misma persona y el mismo espacio, cuando los intervalos son adyacentes? ¿Deben contar las solicitudes `PENDIENTE` y las reservas `APROBADA`, excluyendo `RECHAZADA` y `CANCELADA`?
3. ¿La regla aplica por igual a estudiantes, docentes y usuarios con roles administrativos cuando solicitan para sí mismos?

Estas decisiones se incorporarán a `design.md` y a los escenarios normativos únicamente después de la aprobación del responsable técnico.
