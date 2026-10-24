# Propuesta: interfaz web para reservas académicas

## Why

La entrega actual ofrece una API REST y su documentación OpenAPI. Abrir rutas como `/auth/register` en la barra del navegador envía una petición `GET`, mientras que esa operación requiere `POST`; por eso el navegador muestra `Method Not Allowed`. La API funciona, pero no ofrece una interfaz visual para presentar el flujo institucional.

## What Changes

Se propone incluir una interfaz web sencilla, en español y adaptable a escritorio y móvil, para que estudiantes, docentes y administradores puedan utilizar los casos de uso ya aprobados sin invocar manualmente la API.

La interfaz propuesta cubrirá:

- Registro, inicio/cierre de sesión y visualización del usuario autenticado.
- Consulta de espacios y disponibilidad por fechas.
- Creación de solicitudes, consulta del estado, historial y cancelación permitida.
- Para los roles autorizados: gestión de espacios y revisión de solicitudes con aprobación o rechazo y motivo.
- Mensajes visibles para errores de validación, permisos y conflictos.

La interfaz consumirá las rutas existentes. No se duplicarán las reglas de negocio en el navegador; la API seguirá siendo responsable de autorización y validación.

## Impacto

- **Especificaciones:** se añadirá la capacidad `interfaz-web` con escenarios de acceso, navegación por rol, formularios, errores y consumo de la API. Las capacidades existentes conservarán sus reglas de negocio.
- **Código:** se incorporarán recursos estáticos HTML, CSS y JavaScript servidos por FastAPI, además de rutas para la página inicial y sus recursos. No se propone un framework frontend ni un proceso de compilación independiente.
- **Pruebas:** se añadirán pruebas de rutas y recursos de interfaz, y pruebas de navegador/DOM según la herramienta disponible; los casos API existentes seguirán siendo la verificación de reglas de negocio.
- **Datos existentes:** no se modificará el esquema ni se migrarán datos para la interfaz.
- **Plan:** la interfaz, antes opcional/excluida, pasará a ser parte de la primera entrega si se aprueba este cambio.
- **Dependencias de ejecución:** se corregirá el manifiesto de dependencias para incluir el servidor ASGI que el README ya indica para iniciar la aplicación.

## Dudas que requieren decisión

1. **Implementación visual propuesta:** HTML, CSS y JavaScript sin framework, servidos desde FastAPI, para mantener la instalación sencilla y evitar un segundo stack. La interfaz no reemplazará la API.
2. **Administrador inicial:** una base nueva no contiene cuenta `ADMIN_SISTEMA` y el autorregistro solo crea estudiantes. Se propone añadir un comando local de inicialización que solicite correo y contraseña de forma interactiva y cree el primer administrador solo si aún no existe uno. No habrá credenciales predeterminadas ni alta pública de administradores.
3. **Alcance:** se propone cubrir las operaciones visuales descritas arriba para los roles existentes, sin incluir notificaciones externas, SSO, calendario ni despliegue remoto.

## Criterio para continuar

No se implementará código de interfaz ni de inicialización administrativa hasta que el estudiante revise y apruebe la propuesta y las decisiones de alcance.
