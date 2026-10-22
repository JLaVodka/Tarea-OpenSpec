# Sistema de reservas de espacios académicos

API REST universitaria para administrar espacios, solicitudes de reserva, disponibilidad y decisiones auditadas. La implementación sigue el plan aprobado y las especificaciones OpenSpec del repositorio.

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

## Configuración

Define una clave JWT local de al menos 32 bytes. Para desarrollo puede usarse:

```powershell
$env:JWT_SECRET_KEY = "clave-local-de-desarrollo-con-al-menos-32-bytes"
$env:DATABASE_URL = "sqlite:///./reservas.db"
$env:JWT_ACCESS_TOKEN_MINUTES = "30"
```

`DATABASE_URL` es opcional y usa `sqlite:///./reservas.db` por defecto. Puede apuntar a PostgreSQL con el driver correspondiente cuando el entorno lo instale. No uses la clave de ejemplo en despliegues.

## Crear el esquema y ejecutar

Inicializa el esquema de la base configurada y levanta la API:

```powershell
python -m app.db.init_db
python -m uvicorn app.main:app --reload
```

La API queda en `http://127.0.0.1:8000`; la documentación interactiva está en `http://127.0.0.1:8000/docs`.

## Ejecutar pruebas

```powershell
python -m pytest -q
python -m pytest --cov=app --cov-report=term-missing
```

La suite cubre API, autenticación y permisos, validación de intervalos, solapamientos, dos operaciones concurrentes en SQLite, aprobación/rechazo, cancelación e historial. Las pruebas usan una base temporal; no utilizan la base configurada para la aplicación.

## Rutas principales

| Área | Rutas |
|---|---|
| Usuarios | `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `GET /users` |
| Espacios | `GET /spaces`, `GET /spaces/{id}`, `POST /spaces`, `PUT /spaces/{id}`, `PATCH /spaces/{id}/status`, `DELETE /spaces/{id}` |
| Solicitudes | `POST /reservations`, `GET /reservations`, `GET /reservations/{id}` |
| Decisiones e historial | `POST /reservations/{id}/approve`, `/reject`, `/cancel`, `GET /reservations/{id}/history` |
| Disponibilidad | `GET /availability?space_id=…&starts_at=…&ends_at=…` |

Las operaciones protegidas requieren `Authorization: Bearer <token>`. Las fechas deben usar ISO 8601 con desplazamiento horario, por ejemplo `2030-04-20T09:00:00-05:00`.

## Estructura

```text
app/
  core/          configuración
  db/            SQLAlchemy, sesiones e inicialización del esquema
  users/         cuentas, autenticación y JWT
  roles/         RBAC
  spaces/        catálogo y administración de espacios
  reservations/  solicitudes, disponibilidad, decisiones e historial
tests/           pruebas automatizadas
openspec/        contexto, capacidades y cambios SDD
docs/            trazabilidad entre requisitos, pruebas y código
```

Consulta [PLAN_INGENIERIA.md](PLAN_INGENIERIA.md) para el alcance y las decisiones de arquitectura, y [docs/TRAZABILIDAD.md](docs/TRAZABILIDAD.md) para la relación entre requisitos y pruebas.
