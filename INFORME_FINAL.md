# Informe final — Reservas de espacios académicos

## Resumen del proyecto

Se construyó una aplicación web en español, respaldada por una API REST, para centralizar la administración de espacios universitarios, usuarios y roles, solicitudes, disponibilidad, aprobación/rechazo, cancelaciones e historial auditable. La interfaz HTML/CSS/JavaScript se sirve desde FastAPI y consume la API del mismo origen. La implementación usa FastAPI, SQLAlchemy, Pydantic y SQLite; el diseño de transacciones contempla PostgreSQL.

El trabajo siguió SDD con OpenSpec: se aprobó primero el plan y las especificaciones, se implementó por tareas con pruebas, y la regla institucional de cuatro horas se añadió mediante un change OpenSpec antes de cambiar el código. Después, la solicitud de contar con presentación visual se gestionó con propuesta aprobada, actualización del plan, especificación de interfaz y provisión inicial, validación e implementación. Los changes completados están archivados y las diez capacidades vigentes se encuentran en `openspec/specs/`.

## Resultados de pruebas y cobertura

- Suite completa tras añadir interfaz y provisión administrativa: `114 passed in 21.33s`.
- Cobertura global: **92%** (741 de 807 sentencias cubiertas en la salida con cobertura).
- Los módulos de negocio tienen entre 81% y 100% de cobertura; `app/reservations/service.py` tiene 89% y `app/reservations/router.py` 91%.
- `app/db/init_db.py` aparece con 0% instrumentado porque su ejecución se comprobó por separado mediante la inicialización real del esquema y la prueba HTTP de humo.
- `openspec validate --all --strict`: **10 aprobadas, 0 fallidas** después de archivar la interfaz y la provisión inicial.
- La nueva ruta `/` y los recursos JavaScript, CSS e icono, junto con `/docs`, pasan pruebas HTTP. `node --check app/web/static/app.js` terminó con código 0.
- La interfaz se puede recorrer manualmente siguiendo la sección de demostración del README. Las acciones de navegador automatizadas no se ejecutaron en este entorno; la política del navegador integrado bloqueó la observación de `127.0.0.1`.
- La instalación limpia verificada antes del incremento visual dio `104 passed in 29.62s`; Uvicorn ahora está fijado en `requirements.txt` para que la instalación nueva incluya el servidor necesario.

Las pruebas de concurrencia usan sesiones independientes sobre SQLite. No se ejecutó una instancia PostgreSQL en este entorno, así que el bloqueo `SELECT ... FOR UPDATE` previsto para ese motor no tiene verificación de integración aquí.

## Cumplimiento de requisitos

| Capacidad | Resultado | Evidencia principal |
|---|---|---|
| Usuarios | Implementada | `tests/test_auth.py`; `app/users/`; registro, JWT, contraseñas Argon2 y administración de cuentas |
| Roles y permisos | Implementada | `tests/test_roles_policy.py`; `app/roles/policy.py`; matriz RBAC con ámbitos por espacio |
| Gestión de espacios | Implementada | `tests/test_spaces_api.py`; CRUD, inactividad, ámbito asignado, autoasignación del creador y protección de historial |
| Solicitudes de reserva | Implementada | `tests/test_reservations_api.py`; fechas, espacio activo, duplicados, permisos y consulta por ámbito |
| Disponibilidad | Implementada | `tests/test_reservations_api.py`; solo `APROBADA` bloquea, intervalos semiabiertos y espacios inactivos |
| Prevención de simultaneidad | Implementada en SQLite y diseñada para PostgreSQL | `tests/test_reservation_concurrency.py`, `tests/test_approvals_api.py`; bloqueo transaccional y revalidación antes de insertar/aprobar |
| Aprobación y rechazo | Implementada | `tests/test_approvals_api.py`; ámbito, estados, motivos y eventos auditables |
| Cancelación e historial | Implementada | `tests/test_cancellation_history_api.py`; permisos, motivo administrativo, auditoría cronológica y eventos no mutables por API |
| Regla de cuatro horas | Implementada conforme a decisiones aprobadas | `tests/test_reservations_api.py`, `tests/test_reservation_concurrency.py`; detalle en `openspec/specs/solicitudes-reserva/spec.md` |
| Interfaz web | Implementada; navegación, autenticación, formularios y vistas según rol | `tests/test_web_interface.py`; `app/web/static/`; recorrido visual en README |
| Provisión del primer administrador | Implementada con comando local, hash Argon2, contraseña oculta y rechazo de repetición | `tests/test_initial_admin.py`; `app/users/bootstrap_admin.py` |

La matriz requisito → escenario → prueba → código está en `docs/TRAZABILIDAD.md`.

## Dificultades encontradas

- En Windows, las pruebas `TestClient` necesitan crear hilos de AnyIO. El sandbox inicial bloqueaba ese mecanismo; las ejecuciones verificables se hicieron con el permiso de ejecución elevado autorizado.
- El validador OpenSpec detectó una delta mal clasificada y, después del primer archivado, un requisito demasiado largo. Se corrigió la estructura y se agregó un change documental de refinamiento; la validación estricta final pasa.
- La primera instalación de un entorno limpio no pudo resolver PyPI con la red restringida. Con acceso de red autorizado se instaló el mismo `requirements-dev.txt` en un entorno nuevo y se verificaron esquema, endpoint y pruebas.
- La concurrencia se comprobó solo en SQLite; la comprobación con PostgreSQL queda pendiente de disponer de una instancia de ese motor.
- El navegador integrado no permitió inspeccionar visualmente la página local por su política de acceso a `127.0.0.1`; las rutas y recursos sí se verificaron con TestClient y el recorrido manual quedó documentado para la presentación local.
- Durante la ejecución de la aplicación se descubrió que Uvicorn no estaba declarado en los requisitos aunque el README lo usaba; se añadió como dependencia de ejecución fijada y se validó la suite posterior.

## Decisiones técnicas que cambiaron respecto al plan

| Cambio | Motivo | Impacto |
|---|---|---|
| `httpx` se cambió por `httpx2` manteniendo `TestClient` | La versión de Starlette instalada depreca la integración anterior y recomienda `httpx2`. | Solo afecta dependencias de desarrollo; está registrado como versión 0.2 del plan. |
| Se concretó autenticación con `pwdlib`/Argon2 y PyJWT HS256 | Provee hash de contraseñas y firma JWT sin implementar criptografía propia; las claves vienen de entorno. | Alinea el flujo de usuarios con el stack aprobado. El secreto JWT debe configurarse antes de ejecutar rutas autenticadas. |
| SQLite usa `BEGIN IMMEDIATE` y PostgreSQL contempla bloqueo por fila | Las consultas de conflicto deben serializarse junto con la escritura. | Concurrencia verificada en SQLite; PostgreSQL necesita prueba de integración antes de producción multiinstancia. |
| Se incorporó el máximo de cuatro horas consecutivas | Decisión institucional aprobada: cuatro horas inclusivas; acumular solicitudes pendientes y aprobadas adyacentes por persona/espacio; excluir cuentas administrativas. | Se actualizó el plan a versión 0.3, se modificó la spec antes del código y no requiere migración. |
| Se concretó la estructura modular durante el prototipo | Disponibilidad y auditoría quedaron dentro de `reservations`; no se crearon repositorios separados; algunas operaciones ORM se ejecutan desde rutas. Se evitó añadir módulos que solo reenviaran llamadas SQLAlchemy para este prototipo de un motor. | Aumenta el acoplamiento con SQLAlchemy. El plan versión 0.4 registra la decisión y recomienda extraer repositorios/servicios antes de añadir un motor o escalar el despliegue. |
| Se agregó `python -m app.db.init_db` | El prototipo usa creación controlada del esquema, como permite el plan. | Permite inicializar SQLite antes de arrancar Uvicorn; README verificado desde entorno limpio. |
| Se agregó una interfaz HTML/CSS/JavaScript servida por FastAPI, sin framework frontend | La presentación debía incluir una experiencia visual completa para usar las funciones existentes; un cliente nativo mantiene un solo proceso y evita un segundo despliegue. | Plan versiones 0.5 y 0.6; `/` sirve la aplicación y `/docs` conserva OpenAPI. La API sigue aplicando permisos y validaciones. |
| Se agregó un comando interactivo para provisionar el primer `ADMIN_SISTEMA` y se declaró Uvicorn en los requisitos | Sin cuenta administrativa inicial no se pueden preparar espacios y roles en una base nueva; Uvicorn faltaba del manifiesto usado por el README. | La cuenta inicial no se crea mediante endpoint público ni contraseña predeterminada; las dependencias de una instalación limpia ya incluyen el servidor ASGI. |

## Gestión del cambio de cuatro horas

1. Se documentó el impacto sobre solicitudes, código, pruebas, datos previos y plan en `openspec/changes/archive/2026-10-22-limite-4-horas/`.
2. El responsable técnico decidió que cuatro horas exactas se permiten; las solicitudes `PENDIENTE` y reservas `APROBADA` contiguas se acumulan por persona y espacio; `RECHAZADA` y `CANCELADA` no cuentan; otros usuarios/espacios se calculan por separado; cuentas administradoras quedan excluidas.
3. Se actualizó el plan antes de modificar la spec. El delta OpenSpec se validó y confirmó antes de escribir el código.
4. Las pruebas se escribieron primero y fallaron: la API aceptaba 4h1m y cadenas superiores, y la prueba concurrente permitía insertar ambas solicitudes. Después de implementar la regla, las pruebas de frontera, roles, estados, espacios/personas distintas y concurrencia pasaron.
5. Se archivó el change. El archivado inicial produjo una advertencia de longitud; un change documental posterior separó los requisitos y dejó la spec consolidada válida con `--strict`.

No se alteran datos existentes. Solicitudes `PENDIENTE` y reservas `APROBADA` previas pueden influir en una nueva solicitud contigua; los estados cancelados o rechazados no cuentan.

## SDD con OpenSpec frente a instrucciones directas a una IA

### Ventajas observadas

- La fuente de verdad quedó en requisitos y escenarios versionados antes de implementar las reglas de negocio.
- Los escenarios hicieron explícitos permisos, estados, casos límite y concurrencia; permitieron derivar pruebas trazables.
- Los changes separaron la regla inicial de la regla institucional posterior y conservaron una secuencia revisable en Git.
- `openspec validate --strict` detectó errores de estructura y longitud antes de dar por cerradas las specs.

### Limitaciones observadas

- Redactar y mantener propuestas, deltas, tareas y escenarios tiene un coste documental mayor que pedir una implementación directamente.
- El formato del delta debe respetar exactamente los encabezados OpenSpec; el validador detecta forma y consistencia, pero no decide si la política institucional es correcta.
- Un requisito aprobado todavía necesita revisión humana, pruebas, revisión del diff y validación de seguridad; OpenSpec no garantiza por sí mismo que el código sea correcto.
- Reglas temporales y de concurrencia necesitan decisiones precisas y pruebas ejecutables; una spec ambigua trasladaría esa ambigüedad al código.

## Lecciones aprendidas y conclusiones

La planificación previa ayudó a acordar roles, estados, intervalos y responsabilidades antes de escribir rutas. El enfoque test-first mostró de forma concreta el comportamiento que faltaba y redujo el riesgo de implementar supuestos. La serialización de escrituras fue necesaria tanto para evitar duplicados como para hacer cumplir el nuevo límite consecutivo bajo concurrencia. El cambio de alcance de API a aplicación web también se registró y aprobó en OpenSpec antes de añadir interfaz y configuración inicial de administración.

El sistema cubre el alcance funcional priorizado y puede instalarse localmente siguiendo el README. La entrega incluye una interfaz web para presentar los flujos principales, además de la API y la documentación. Antes de un despliegue institucional se debe probar PostgreSQL, revisar el acoplamiento ORM documentado, definir zona horaria/anticipación/horarios hábiles, gestionar secretos de producción y decidir respaldos y retención de auditoría.

## Preguntas de sustentación

> **Revisar y personalizar todas estas respuestas con la experiencia real del estudiante antes de presentar.** Son borradores basados en el historial del proyecto.

### ¿Qué decisiones se tomaron antes de programar?

Se definió un monolito modular para una API institucional pequeña y luego se amplió mediante un change aprobado para incluir una interfaz web, el stack FastAPI/SQLAlchemy/SQLite, actores y responsabilidades iniciales, estados de reserva, intervalos semiabiertos y el uso de OpenSpec como fuente de verdad. Las políticas no decididas se registraron para consultarlas antes de implementarlas.

### ¿Qué problemas aparecieron al convertir el plan en especificaciones?

Fue necesario concretar permisos por rol y ámbito, distinguir solicitudes pendientes de reservas aprobadas y definir atomicidad para evitar carreras. Más adelante se detectó que una regla aprobada podía hacer demasiado largo un requisito; se separó en requisitos y escenarios y se volvió a validar.

### ¿Cómo se evitó que la IA implementara funcionalidades incorrectas?

Se implementó después de revisar y aprobar specs, se trabajó tarea por tarea, se escribieron pruebas derivadas de escenarios, se revisaron diffs y se validó OpenSpec. Cuando apareció la política de cuatro horas y después la necesidad de la interfaz, se actualizaron plan y specs antes de modificar servicios o presentación.

### ¿Qué diferencias hubo entre planificación e implementación?

El plan propuso paquetes separados para repositorios, disponibilidad e historial. En el prototipo, disponibilidad e historial se agruparon en reservas y algunas operaciones usan SQLAlchemy desde rutas. Se documentó la justificación y el costo de acoplamiento en la versión 0.4 del plan. La interfaz se añadió después en la versión 0.5 y su estructura real se registró en 0.6, junto con provisión del primer administrador y Uvicorn declarado. También se reemplazó `httpx` por `httpx2` por compatibilidad con Starlette.

### ¿Qué ventajas y limitaciones tiene SDD frente a dar instrucciones directas a una IA?

SDD ofrece requisitos versionados, decisiones explícitas, trazabilidad y una base para pruebas y revisión. Añade trabajo documental y depende de que las specs sean claras; los validadores verifican estructura, no la corrección de decisiones de negocio ni la calidad total del código.

**Personalizar:** añadir qué decisión fue más difícil, qué prueba reveló un error inesperado y qué aprendizaje corresponde a la experiencia individual durante la actividad.
