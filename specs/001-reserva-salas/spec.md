# Especificación — Sistema de Reserva de Salas

## 1. Objetivo
Construir un sistema web responsive para gestionar reservas de salas en una institución educativa.

## 2. Problema
El proceso actual se realiza mediante correo electrónico y Excel, dificultando la consulta de disponibilidad, los controles automáticos y la prevención de conflictos.

## 3. Alcance MVP
### Incluido
Autenticación; roles/permisos; disponibilidad; creación de reservas; reglas de negocio; cancelación; historial; reserva asistida por Secretaría; gestión básica de salas; reportes; No-Show; bloqueo de 3 días; auditoría.

### Fuera del MVP
Aplicación móvil nativa; integración obligatoria con sistema académico existente; WhatsApp como dependencia obligatoria; integraciones externas no definidas.

## 4. Requisitos
- RF01: autenticación.
- RF02: validación de alumno regular para reserva asistida.
- RF03: consulta de disponibilidad por fecha.
- RF04: capacidad y características de sala.
- RF05: creación de reserva.
- RF06: prevención de conflicto sala/fecha/hora.
- RF07: validación de capacidad.
- RF08: máximo 2 reservas diarias.
- RF09: prevención de solapamiento/consecutividad.
- RF10: cancelación.
- RF11: regla de 24 horas.
- RF12: historial.
- RF13: confirmación por correo, si se prioriza para implementación.
- RF14: reportes.
- RF15: gestión de salas.
- RF16: usuarios/permisos.
- RF17: registro de No-Show.
- RF18: bloqueo temporal de 3 días.
- RF19: cada reserva individual tiene una duración máxima de 1 hora. Esta regla se valida en backend para reservas directas y asistidas.

## 5. Casos de uso
- CU01 Autenticación — Usuario.
- CU02 Consultar disponibilidad — Alumno.
- CU03 Gestionar reserva — Alumno; Secretaría en reserva asistida.
- CU04 Cancelar reserva — Alumno/usuario autorizado según permisos.
- CU05 Historial, reportes y No-Show — según operación y permisos.

## 6. Entidades mínimas
Usuario/Perfil, Alumno, Sala, Reserva y Auditoría. Se pueden separar o extender si existe justificación y se actualiza la documentación.

## 7. Seguridad
Django Auth, autorización por rol, CSRF, validación de entradas, protección de datos, contraseñas gestionadas por Django, secretos fuera del repositorio y auditoría de acciones sensibles.

## 8. UX
Interfaz clara, responsive, consistente, con mensajes de error comprensibles y acciones según rol.

## 9. Criterios de aceptación
Una reserva válida pertenece a usuario autenticado, dura como máximo 1 hora, usa sala disponible, respeta capacidad y máximo diario, no genera solapamiento ni consecutividad y no está impedida por bloqueo. Debe quedar `CONFIRMADA`.

La nueva duración máxima aplica a reservas creadas después del cambio; no cancela automáticamente reservas ya confirmadas.

Una reserva inválida debe rechazarse indicando la causa.

## 10. Pruebas
CP01–CP21. CP21 verifica que una reserva de 1 hora sea válida y que una duración mayor se rechace tanto en el formulario como en el servicio backend. Los resultados se completarán después de ejecutar el prototipo.
