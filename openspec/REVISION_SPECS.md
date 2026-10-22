# Revisión de especificaciones — capacidades iniciales de reservas

## Alcance de la revisión

Se contrastaron las ocho capacidades del change `bootstrap-reservas` entre sí y con `PLAN_INGENIERIA.md`. Esta revisión no incluye código. Los ajustes de este documento se aplicaron a los deltas antes de iniciar la implementación.

## Verificación de consistencia

| Tema | Regla consistente tras la revisión | Evidencia en specs |
|---|---|---|
| Roles | `ESTUDIANTE`, `DOCENTE`, `ADMIN_ESPACIOS` y `ADMIN_SISTEMA`. Los permisos se combinan por unión si la cuenta posee varios roles; cada permiso conserva su ámbito. `ADMIN_SISTEMA` solo no aprueba ni administra espacios ni consulta auditoría de reservas. | `design.md`; `roles-permisos/spec.md`; `gestion-espacios/spec.md`; `aprobacion-rechazo/spec.md`; `cancelacion-historial/spec.md` |
| Asignación | `ADMIN_SISTEMA` asigna roles y el ámbito de espacios a administradores; no puede elevar sus propios permisos. No hay permisos individuales que contradigan la matriz. | `design.md`; `usuarios/spec.md`; `roles-permisos/spec.md` |
| Estados | Una solicitud nace `PENDIENTE`; transiciones terminales válidas: `APROBADA`, `RECHAZADA` o `CANCELADA`. No se permite decidir de nuevo un estado terminal. | `solicitudes-reserva/spec.md`; `aprobacion-rechazo/spec.md`; `cancelacion-historial/spec.md` |
| Disponibilidad | Solo `APROBADA` bloquea disponibilidad. `PENDIENTE`, `RECHAZADA` y `CANCELADA` no bloquean. Una solicitud nueva sí se rechaza si se solapa con una aprobación existente. | `design.md`; `solicitudes-reserva/spec.md`; `disponibilidad/spec.md` |
| Duplicidad pendiente | Personas distintas pueden dejar solicitudes solapadas pendientes; la misma persona no puede crear dos solicitudes pendientes solapadas del mismo espacio. La decisión se confirmó durante la revisión. | `design.md`; `solicitudes-reserva/spec.md` |
| Tiempo | Entradas ISO 8601 con offset obligatorio, normalizadas a UTC. Intervalos semiabiertos `[inicio, fin)`: inicio `<` fin y el inicio debe ser estrictamente posterior al momento de recepción. Adyacencia permitida. | `design.md`; `solicitudes-reserva/spec.md`; `disponibilidad/spec.md`; `prevencion-reservas-simultaneas/spec.md` |
| Solapamiento y carrera | Mismo espacio: `nuevo_inicio < existente_fin AND existente_inicio < nuevo_fin`. La creación comprueba aprobaciones y duplicados propios de forma atómica; la aprobación revalida de forma atómica para cerrar carreras. | `design.md`; `solicitudes-reserva/spec.md`; `prevencion-reservas-simultaneas/spec.md`; `aprobacion-rechazo/spec.md` |
| Espacio inactivo | No acepta nuevas solicitudes ni se presenta como reservable. Desactivarlo no cambia reservas existentes ni elimina su historial. | `design.md`; `gestion-espacios/spec.md`; `solicitudes-reserva/spec.md`; `disponibilidad/spec.md` |
| Borrado | El borrado físico solo se permite a administrador asignado si no existe ninguna solicitud/reserva relacionada; con referencias se conserva y se desactiva. | `design.md`; `gestion-espacios/spec.md` |
| Cancelación | El solicitante cancela solicitudes propias pendientes o aprobadas sin plazo límite. El administrador asignado puede forzarla con motivo no vacío tras recortar espacios externos; la cancelación libera una franja aprobada. | `design.md`; `cancelacion-historial/spec.md`; matriz de `design.md` |
| Auditoría | Creación, aprobación, rechazo y cancelación registran actor y momento; rechazo y cancelación administrativa conservan motivo. El solicitante ve lo propio y el administrador de espacios solo su ámbito. | `aprobacion-rechazo/spec.md`; `cancelacion-historial/spec.md` |

## Ambigüedades encontradas y resolución

| Ambigüedad | Resolución aplicada | Cómo se resolvió |
|---|---|---|
| Forma de alta y rol inicial | Autorregistro con rol `ESTUDIANTE`; el usuario no puede elegirse roles privilegiados. | Respuesta explícita del responsable técnico durante esta revisión. |
| Una solicitud pendiente idéntica o solapada del mismo usuario | Se rechaza si es del mismo espacio y solicitante. Solapamientos pendientes entre solicitantes distintos pueden coexistir. | Respuesta explícita del responsable técnico durante esta revisión. |
| Quién cancela y con qué condiciones | El solicitante cancela sus propias solicitudes pendientes/aprobadas sin plazo. El administrador asignado puede cancelar con motivo obligatorio. | Respuesta explícita del responsable técnico durante esta revisión. |
| Normalización del correo de registro | Quitar espacios externos y comparar correo sin distinguir mayúsculas para detectar duplicados. | Criterio técnico para que la unicidad sea verificable y estable. |
| Quién asigna ámbito de espacios | `ADMIN_SISTEMA` asigna espacios a cuentas con rol `ADMIN_ESPACIOS`; un usuario no puede elevar su propia asignación. | Aclaración necesaria para que el ámbito por espacio tenga un actor y un escenario verificables. |
| ¿El administrador del sistema hereda facultades de negocio? | No. Se aplican solo los permisos del rol de espacios; roles combinados suman permisos, pero cada uno conserva su ámbito. | Aclaración de consistencia con la separación entre administración técnica y de espacios del plan aprobado. |
| ¿Qué hacer con inicio igual al momento actual? | Se rechaza: el inicio debe ser estrictamente futuro (`inicio > ahora`). | Corrección aplicada para que “futuro” sea verificable y no dependa de interpretación. |
| ¿Se borra un espacio con solicitudes rechazadas o canceladas? | No se borra físicamente si existe cualquier solicitud/reserva relacionada; se desactiva. | Corrección aplicada para preservar todas las referencias e historial. |
| ¿Se bloquea disponibilidad por solicitudes pendientes? | No. Solo aprobadas bloquean. La creación comprueba aprobaciones y duplicados propios; las solicitudes distintas pendientes pueden coexistir y se revalida al aprobar. | Regla coherente con el flujo de aprobación del plan, explicitada en escenarios. |
| ¿Puede un administrador asignado administrar cualquier espacio? | Solo espacios asignados; el administrador del sistema mantiene asignaciones. | Ámbito ya indicado en el plan, concretado en matriz y escenarios negativos. |

## Contradicciones detectadas y correcciones aplicadas

1. Algunas frases concedían al rol `ADMIN_SISTEMA` permisos especiales por “permiso explícito”, pero la matriz no definía cómo asignarlos. Se quitaron los permisos directos no modelados y se estableció que la cuenta requiere también el rol de negocio correspondiente.
2. El diseño rechazaba solo fechas pasadas, mientras un escenario exigía fecha futura. Se hizo uniforme: `inicio > ahora`; igualdad también se rechaza.
3. El criterio de borrado variaba entre “sin reservas” y “sin solicitudes ni reservas”. Se unificó para proteger cualquier fila relacionada.
4. El texto permitía cancelación administrativa “si su permiso lo permite” sin definirlo en la matriz. Se concretó con motivo obligatorio para administradores asignados.
5. El problema menciona solicitudes duplicadas, pero la spec permitía solicitudes propias duplicadas. Se agregó prevención de duplicado pendiente propio sin bloquear solicitudes de otras personas.
6. La matriz limitaba administradores de espacios a espacios asignados pero no especificaba quién administra la asignación. Se añadió al contrato de administración de cuentas que solo `ADMIN_SISTEMA` asigna esos ámbitos y no puede autoasignárselos.
7. La regla anti-duplicado propio podía fallar con dos registros concurrentes si la comprobación se separaba de la inserción. Se exigió atomicidad y un escenario de concurrencia para creación.

## Correspondencia PLAN_INGENIERIA.md ↔ specs

| Sección del plan | Capacidad respaldada | Cobertura |
|---|---|---|
| 1. Análisis: actores y alcance | `usuarios`, `roles-permisos`, `gestion-espacios` | Estudiantes, docentes y administradores con ámbitos separados. |
| 2. Propuesta: módulos espacios, usuarios, roles, reservas, disponibilidad, aprobación, historial | Las ocho capacidades | Una delta por módulo; relaciones y comportamiento enlazados. |
| 2. Funcionalidades Must: catálogo y ciclo de reserva | `gestion-espacios`, `solicitudes-reserva`, `disponibilidad`, `prevencion-reservas-simultaneas`, `aprobacion-rechazo`, `cancelacion-historial` | Camino feliz, denegaciones y bordes. |
| 3. Arquitectura, entidades y transacciones | `usuarios`, `roles-permisos`, `solicitudes-reserva`, `prevencion-reservas-simultaneas`, `cancelacion-historial` | Contratos de dominio y atomicidad; no se prescribe código en esta fase. |
| 4. Desarrollo SDD e incrementos | Todas | El change agrupa capacidades y tareas ordenadas por dependencia. |
| 5. Calidad y riesgos de solapamiento/permisos/fechas | `roles-permisos`, `disponibilidad`, `prevencion-reservas-simultaneas`, `aprobacion-rechazo` | Escenarios negativos, adyacencia y carrera concurrente. |
| 6. OpenSpec, revisión humana y trazabilidad | Todas | Requisitos normativos, escenarios y revisión previa a implementación. |

**Falta o sobra:** no se especifican interfaz gráfica, calendarios, notificaciones ni SSO, en consistencia con el alcance excluido. La regla máxima de cuatro horas no se incluye en este change inicial: está reservada para la fase posterior de cambio de negocio. No se detectaron requisitos fuera del alcance aprobado.

## Cambios al plan

No cambia la arquitectura, el stack ni el alcance del plan. Las decisiones aquí concretan permisos y reglas operativas dentro de los supuestos ya aprobados; no se requiere nueva entrada en el historial de `PLAN_INGENIERIA.md`.

## Estado previo a implementación

La revisión de consistencia y las aclaraciones están aplicadas. `tasks.md` contiene las tareas de implementación en orden de dependencias y con referencias a requisitos. La implementación sigue bloqueada hasta aprobación expresa de esta revisión.
