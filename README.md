# Sistema de reservas de espacios académicos

Aplicación universitaria para administrar espacios, solicitudes de reserva, disponibilidad y decisiones auditadas. Incluye una interfaz web en español y una API REST; la implementación sigue el plan aprobado y las especificaciones OpenSpec del repositorio.

## Requisitos

- Python 3.11 o posterior.
- pip.
- SQLite incluido en Python para desarrollo y pruebas.

## Instalación en Windows (PowerShell)

Desde la raíz del repositorio:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

En Linux/macOS, sustituye la activación por `source .venv/bin/activate`.

Si PowerShell bloquea `Activate.ps1`, no es necesario cambiar la política del sistema. Usa directamente el intérprete del entorno en cada comando: `.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt`, `.\.venv\Scripts\python.exe -m ...`.

## Configuración

Define una clave JWT local de al menos 32 bytes. Para desarrollo puede usarse:

```powershell
$env:JWT_SECRET_KEY = "clave-local-de-desarrollo-con-al-menos-32-bytes"
$env:DATABASE_URL = "sqlite:///./reservas.db"
$env:JWT_ACCESS_TOKEN_MINUTES = "30"
```

`DATABASE_URL` es opcional y usa `sqlite:///./reservas.db` por defecto. Puede apuntar a PostgreSQL con el driver correspondiente cuando el entorno lo instale. No uses la clave de ejemplo en despliegues.

## Crear el esquema, administrador inicial y ejecutar

Inicializa el esquema de la base configurada y crea el primer administrador del sistema. El comando solicita el correo y una contraseña oculta; solo funciona si todavía no existe un `ADMIN_SISTEMA`:

```powershell
python -m app.db.init_db
python -m app.users.bootstrap_admin
python -m uvicorn app.main:app --reload
```

La aplicación visual queda en `http://127.0.0.1:8000`; la documentación interactiva de la API está en `http://127.0.0.1:8000/docs`. No abras `/auth/register` en la barra del navegador: es una ruta API que requiere `POST`; el registro visual está en la página raíz.

En PowerShell, si no activaste el entorno virtual, cambia `python` por `.\.venv\Scripts\python.exe` en estos comandos. En Linux/macOS puedes usar `python` después de activar el entorno.

## Recorrido visual de demostración

1. Abre `http://127.0.0.1:8000/` y crea cuentas desde el formulario de registro; el autorregistro asigna el rol `ESTUDIANTE`.
2. Inicia sesión con el administrador inicial. En **Administración → Cuentas y roles**, asigna `ADMIN_ESPACIOS` a una de las cuentas creadas.
3. Cierra sesión e inicia con esa cuenta de administrador de espacios. En **Administración**, crea un laboratorio, auditorio o sala; quien crea el espacio queda asignado automáticamente.
4. Inicia con otra cuenta de estudiante, consulta el espacio y horario, y envía una solicitud desde **Mis solicitudes**.
5. Vuelve a iniciar como administrador de espacios para aprobar o rechazar la solicitud. El estudiante puede consultar el estado y el historial en su sesión.

La interfaz también permite desactivar espacios, administrar cuentas, asignar administradores a espacios y consultar/cancelar solicitudes según los permisos del servidor. Si un control no corresponde al ámbito asignado, la API devuelve una denegación y la interfaz muestra el mensaje.

## Ejecutar pruebas

```powershell
python -m pytest -q
python -m pytest --cov=app --cov-report=term-missing
```

Si no activaste `.venv` en PowerShell, ejecuta `.\.venv\Scripts\python.exe -m pytest -q` y `.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing`.

La suite cubre interfaz y recursos estáticos, provisión inicial segura, API, autenticación y permisos, validación de intervalos, solapamientos, operaciones concurrentes en SQLite, aprobación/rechazo, cancelación e historial. Las pruebas usan una base temporal; no utilizan la base configurada para la aplicación.

## Rutas principales

| Área | Rutas |
|---|---|
| Usuarios | `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `GET /users` |
| Espacios | `GET /spaces`, `GET /spaces/{id}`, `POST /spaces`, `PUT /spaces/{id}`, `PATCH /spaces/{id}/status`, `DELETE /spaces/{id}` |
| Solicitudes | `POST /reservations`, `GET /reservations`, `GET /reservations/{id}` |
| Decisiones e historial | `POST /reservations/{id}/approve`, `/reject`, `/cancel`, `GET /reservations/{id}/history` |
| Disponibilidad | `GET /availability?space_id=…&starts_at=…&ends_at=…` |

Las operaciones protegidas requieren `Authorization: Bearer <token>`. Las fechas deben usar ISO 8601 con desplazamiento horario, por ejemplo `2030-04-20T09:00:00-05:00`.

Para solicitudes de cuentas sin rol administrativo se permite una duración máxima inclusiva de cuatro horas consecutivas en el mismo espacio. El sistema acumula solicitudes `PENDIENTE` y reservas `APROBADA` contiguas de la misma persona; solicitudes rechazadas/canceladas, otras personas y otros espacios no suman. Las cuentas con rol administrativo están exentas según las reglas aprobadas en OpenSpec.

## Estructura

```text
app/
  core/          configuración
  db/            SQLAlchemy, sesiones e inicialización del esquema
  users/         cuentas, autenticación y JWT
  roles/         RBAC
  spaces/        catálogo y administración de espacios
  reservations/  solicitudes, disponibilidad, decisiones e historial
  web/static/    interfaz HTML, CSS, JavaScript e icono local
tests/           pruebas automatizadas
openspec/        contexto, capacidades y cambios SDD
docs/            trazabilidad entre requisitos, pruebas y código
```

Consulta [PLAN_INGENIERIA.md](PLAN_INGENIERIA.md) para el alcance y las decisiones de arquitectura, y [docs/TRAZABILIDAD.md](docs/TRAZABILIDAD.md) para la relación entre requisitos y pruebas.
