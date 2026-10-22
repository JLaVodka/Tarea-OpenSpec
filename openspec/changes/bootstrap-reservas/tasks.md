# Tareas de implementación: capacidades iniciales de reservas

## 1. Fundación y persistencia

- [x] 1.1 Crear la estructura modular FastAPI, configuración por entorno y sesión SQLAlchemy para SQLite. (Req: todas las capacidades)
- [x] 1.2 Escribir fixtures con base SQLite aislada y configuración de dependencias para la API. (Req: todas las capacidades)
- [x] 1.3 Definir modelos y relaciones de usuarios, roles y permisos, con unicidad de correo normalizado. (Req: usuarios — Registrar estudiantes; Administrar cuentas; roles-permisos — Combinar roles y denegar por defecto)
- [x] 1.4 Definir modelos de espacios, reservas y eventos, claves foráneas e índices de consulta. (Req: gestion-espacios; solicitudes-reserva; cancelacion-historial — Consultar historial auditado)

## 2. Usuarios y autenticación

- [ ] 2.1 Escribir pruebas de registro, correo normalizado duplicado, rol inicial, credenciales, cuenta inactiva, token inválido/expirado y autoasignación de permisos. (Req: usuarios — Registrar estudiantes; Administrar cuentas; Autenticar sin exponer secretos)
- [ ] 2.2 Implementar repositorio y servicios de alta, hash de contraseña, autenticación JWT, administración de cuentas, roles y asignaciones de espacios. (Req: usuarios — Registrar estudiantes; Administrar cuentas; Autenticar sin exponer secretos)

## 3. Roles y permisos

- [ ] 3.1 Escribir pruebas positivas/negativas para solicitantes, matriz por rol, ámbito asignado, roles combinados y denegación por defecto. (Req: roles-permisos — Autorizar operaciones de solicitantes; Limitar administración al ámbito de espacios; Limitar el rol de administrador del sistema; Combinar roles y denegar por defecto)
- [ ] 3.2 Implementar asignación administrativa de roles y espacios, autorización por unión de roles y controles de ámbito. (Req: usuarios — Administrar cuentas; roles-permisos — Limitar administración al ámbito de espacios; Limitar el rol de administrador del sistema; Combinar roles y denegar por defecto)

## 4. Gestión de espacios

- [ ] 4.1 Escribir pruebas de CRUD, datos requeridos, capacidad inválida, estado inactivo, permisos y borrado con/sin referencias. (Req: gestion-espacios — Administrar espacios; Preservar integridad del espacio)
- [ ] 4.2 Implementar CRUD de espacios, asignación de responsables, desactivación y borrado físico condicionado a ausencia de solicitudes. (Req: gestion-espacios — Administrar espacios; Preservar integridad del espacio)

## 5. Solicitudes y disponibilidad

- [ ] 5.1 Escribir pruebas de solicitud válida, fechas inválidas/pasadas/iguales a ahora, falta de offset, espacio inactivo, aprobaciones conflictivas, duplicado propio, solicitantes distintos y duplicado concurrente. (Req: solicitudes-reserva — Crear solicitud válida; Evitar duplicados propios concurrentes)
- [ ] 5.2 Implementar creación atómica y consulta de solicitudes con ámbito por solicitante/administrador y validación de conflictos/duplicados. (Req: solicitudes-reserva — Crear solicitud válida; Consultar solicitudes; Evitar duplicados propios concurrentes)
- [ ] 5.3 Escribir pruebas de consulta libre, conflicto exacto/parcial, adyacencia, estados no bloqueantes, espacio inactivo y falta de autenticación. (Req: disponibilidad — Consultar disponibilidad; No ofrecer espacios inactivos como reservables)
- [ ] 5.4 Implementar consulta de disponibilidad usando intervalos semiabiertos y solo reservas aprobadas como bloqueo. (Req: disponibilidad — Consultar disponibilidad; No ofrecer espacios inactivos como reservables)

## 6. Prevención de reservas simultáneas

- [ ] 6.1 Escribir pruebas de coincidencia exacta, solapamiento parcial, adyacencia, espacios diferentes, cancelación del conflicto y aprobación concurrente. (Req: prevencion-reservas-simultaneas — Detectar solapamiento; Comprobar y escribir atómicamente)
- [ ] 6.2 Implementar validación y transición atómicas para impedir doble aprobación en SQLite; documentar límites del mecanismo. (Req: prevencion-reservas-simultaneas — Comprobar y escribir atómicamente)

## 7. Aprobación y rechazo

- [ ] 7.1 Escribir pruebas de aprobación permitida/denegada, estados no pendientes, espacio inactivo, administrador fuera de ámbito y motivo de rechazo. (Req: aprobacion-rechazo — Aprobar solicitud pendiente; Rechazar con motivo)
- [ ] 7.2 Implementar transiciones de aprobación/rechazo con actor, fecha, motivo y revalidación de disponibilidad dentro de la transacción. (Req: aprobacion-rechazo — Aprobar solicitud pendiente; Rechazar con motivo)

## 8. Cancelación e historial

- [ ] 8.1 Escribir pruebas de cancelación propia sin plazo, cancelación administrativa con/sin motivo, estados no cancelables y ámbito. (Req: cancelacion-historial — Cancelar reserva)
- [ ] 8.2 Implementar cancelación por solicitante o administrador asignado, liberar disponibilidad y registrar eventos auditables. (Req: cancelacion-historial — Cancelar reserva; Consultar historial auditado)
- [ ] 8.3 Escribir pruebas de consulta cronológica del historial, permisos por ámbito e inmutabilidad desde la API. (Req: cancelacion-historial — Consultar historial auditado)
- [ ] 8.4 Implementar consulta de historial y protección de eventos contra modificación/eliminación por la API. (Req: cancelacion-historial — Consultar historial auditado)

## 9. Integración y trazabilidad

- [ ] 9.1 Ejecutar suite completa tras cada grupo, corregir regresiones y registrar salidas reales. (Req: todas las capacidades)
- [ ] 9.2 Actualizar `docs/TRAZABILIDAD.md` con cada requisito, escenario, prueba y archivo de código implementado. (Req: todas las capacidades)
- [ ] 9.3 Completar README de instalación/ejecución y revisar el diff contra este change aprobado. (Req: todas las capacidades)
