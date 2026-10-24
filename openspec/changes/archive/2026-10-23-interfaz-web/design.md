# Diseño propuesto: interfaz web para reservas académicas

## Contexto

El backend ya expone operaciones HTTP y genera OpenAPI, pero no define una pantalla de presentación. La solicitud nueva requiere que el sistema sea demostrable mediante una aplicación visual completa.

## Decisión propuesta

Servir una interfaz de una sola página ligera desde el mismo proceso FastAPI usando archivos estáticos HTML, CSS y JavaScript. El navegador consumirá la API del mismo origen. Las reglas de permisos, disponibilidad, solapamiento, duración y transiciones de estado permanecerán en el backend.

### Alternativas consideradas

- **React/Vue con compilación separada:** descartada para este incremento porque añade runtime, dependencias, configuración de build y despliegue de dos componentes sin ser necesaria para los formularios y tablas requeridos.
- **Plantillas renderizadas en servidor:** descartadas porque la API ya está diseñada como REST y una pequeña interfaz cliente permite reutilizarla directamente.
- **Usar solamente `/docs`:** descartada como experiencia de usuario final porque es una herramienta de exploración técnica de API, no una interfaz del sistema institucional.

## Navegación y permisos

- Visitantes: registro e inicio de sesión.
- Estudiantes/docentes: espacios, consulta de disponibilidad, nueva solicitud, solicitudes propias, detalle/historial y cancelación cuando la API lo permita.
- Administradores de espacios: espacios asignados, gestión autorizada del catálogo y cola de solicitudes para aprobar/rechazar.
- Administrador del sistema: administración de cuentas/roles existente.

La interfaz ocultará acciones que no correspondan a los roles visibles, pero esto solo mejora la navegación; el backend seguirá denegando solicitudes no autorizadas.

## Sesión

Se propone conservar el token JWT en `sessionStorage`, enviarlo como `Authorization: Bearer` en peticiones protegidas y eliminarlo al cerrar sesión o ante una respuesta de autenticación inválida. No se almacenará la contraseña después de iniciar sesión.

## Provisión inicial de administración

La instalación no puede administrar espacios ni usuarios hasta contar con un administrador del sistema. Se propone un comando interactivo local para crear esa cuenta inicial con hash de contraseña existente; no expondrá un endpoint público ni incluirá una contraseña predeterminada. Debe ser idempotente o rechazar una segunda ejecución si ya hay administrador.

## Pruebas propuestas

- Pruebas de integración para servir la página y recursos estáticos.
- Pruebas automatizadas de las funciones JavaScript para validación y renderizado si el entorno disponible lo permite; en caso contrario, documentar verificación manual reproducible y mantener cobertura API automatizada.
- Recorrido manual documentado en README: iniciar sesión, consultar espacios/disponibilidad, crear solicitud y revisar su estado; recorrido administrativo tras aprovisionar el administrador.
- Suite API completa para confirmar que la interfaz no altera las reglas ya aprobadas.

## Consecuencias

- La aplicación podrá presentarse en navegador en la ruta `/` y la documentación técnica seguirá en `/docs`.
- Se añade una superficie de interfaz que debe mantenerse accesible, con formularios etiquetados y mensajes claros.
- La persistencia del token en `sessionStorage` limita su permanencia a la pestaña, pero sigue expuesta a XSS; la interfaz deberá evitar HTML no confiable y no presentarse como endurecida para producción sin revisión de seguridad adicional.
- El cambio no convierte SQLite ni la configuración local en una solución desplegada para producción.
