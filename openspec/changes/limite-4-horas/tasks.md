# Tareas del cambio: límite de cuatro horas consecutivas

## 1. Regla de duración y continuidad

- [x] 1.1 Escribir pruebas de cuatro horas exactas, cuatro horas y un minuto, cadena contigua pendiente/aprobada, estados rechazado/cancelado, mismo usuario en espacios distintos, otra persona, exención administrativa y mensaje claro. (Req: solicitudes-reserva — Crear solicitud válida; Limitar reservas consecutivas a cuatro horas)
- [x] 1.2 Implementar el cálculo de duración individual y cadena contigua para el mismo solicitante/espacio dentro de la transacción de creación. (Req: solicitudes-reserva — Crear solicitud válida; Limitar reservas consecutivas a cuatro horas)

## 2. Concurrencia y regresión

- [x] 2.1 Escribir una prueba concurrente de solicitudes propias contiguas que individualmente cumplen el máximo, pero juntas lo exceden. (Req: solicitudes-reserva — Comprobar el límite consecutivo atómicamente)
- [x] 2.2 Aplicar el bloqueo existente, ejecutar suite completa con cobertura, corregir regresiones y registrar la salida real. (Req: solicitudes-reserva — Comprobar el límite consecutivo atómicamente; todas las capacidades)
- [ ] 2.3 Actualizar `docs/TRAZABILIDAD.md`, archivar el change y validar las specs consolidadas en modo estricto. (Req: todas las capacidades)
