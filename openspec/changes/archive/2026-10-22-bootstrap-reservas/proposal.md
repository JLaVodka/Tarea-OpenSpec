# Propuesta: capacidades iniciales de reservas

## Why

La institución gestiona reservas por correo y hojas de cálculo, lo que dificulta consultar disponibilidad, controlar permisos y evitar conflictos. Se propone acordar el comportamiento mínimo de la API antes de escribir código.

## What Changes

- Se especifican ocho capacidades: espacios, usuarios, roles/permisos, solicitudes, disponibilidad, prevención de reservas simultáneas, aprobación/rechazo y cancelación/historial.
- Se fijan los estados de reserva, el cálculo de solapamiento y los permisos derivados del plan aprobado.
- Se establece autorregistro de estudiantes; los roles de docente y administrativos se asignan mediante administración autorizada.
- Ningún código funcional se incluye en este change.

## Capabilities

### New Capabilities
- `gestion-espacios`: catálogo y ciclo de vida de espacios académicos.
- `usuarios`: autorregistro de estudiantes, administración y autenticación.
- `roles-permisos`: autorización basada en roles para acciones del sistema.
- `solicitudes-reserva`: creación y validación de solicitudes.
- `disponibilidad`: consulta de intervalos libres por espacio.
- `prevencion-reservas-simultaneas`: rechazo de solapamientos incluso bajo concurrencia.
- `aprobacion-rechazo`: decisión administrativa y estados de reserva.
- `cancelacion-historial`: cancelación autorizada y consulta de historial auditable.

## Impact

- Afecta únicamente las especificaciones OpenSpec iniciales y su contexto.
- Establece contratos que después se implementarán en FastAPI, servicios, repositorios y SQLAlchemy.
- Requiere pruebas de permisos, bordes temporales, flujo de estados y concurrencia antes de considerar implementada cada capacidad.
- Las políticas institucionales no definidas en el plan (zona local, duración máxima, anticipación, horario hábil y retención) siguen fuera de esta definición inicial.
