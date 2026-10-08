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
- RF13: enviar confirmación por correo después de crear satisfactoriamente una reserva, cuando el alumno tenga una dirección válida. SMTP se configura mediante variables de entorno.
- RF14: reportes para Secretaría y Administración con filtros por fecha y sala; mostrar reservas por estado, sala y período, bloqueos vigentes y horas de reservas confirmadas. Las horas reservadas no representan porcentaje de ocupación porque no se definen horarios de disponibilidad por sala.
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
Django Auth, autorización por rol, CSRF, validación de entradas, protección de datos, contraseñas gestionadas por Django con mínimo de 8 caracteres y mayúscula, minúscula, número y carácter especial, bloqueo temporal ante intentos fallidos, secretos fuera del repositorio y auditoría de acciones sensibles.

## 8. UX
Interfaz clara, responsive, consistente, con mensajes de error comprensibles y acciones según rol.

## 9. Criterios de aceptación
Una reserva válida pertenece a usuario autenticado, dura como máximo 1 hora, usa sala disponible, respeta capacidad y máximo diario, no genera solapamiento ni consecutividad y no está impedida por bloqueo. Debe quedar `CONFIRMADA`.

La nueva duración máxima aplica a reservas creadas después del cambio; no cancela automáticamente reservas ya confirmadas.

Una reserva inválida debe rechazarse indicando la causa.

## 10. Pruebas
Casos de prueba:
- CP01 inicio de sesión correcto.
- CP02 límite de intentos fallidos y bloqueo temporal.
- CP03 consulta de disponibilidad.
- CP04 reserva válida.
- CP05 capacidad máxima.
- CP06 concurrencia ante intentos simultáneos (requiere validar contra PostgreSQL).
- CP07 conflicto de sala.
- CP08 máximo de dos reservas diarias.
- CP09 cancelación con menos de 24 horas.
- CP10 cancelación con al menos 24 horas.
- CP11 reserva asistida.
- CP12 entradas de filtros tratadas como datos (sin inyección SQL).
- CP13 historial y autorización de lectura.
- CP14 registro de auditoría.
- CP15 correo de confirmación.
- CP16 autorización por rol.
- CP17 regresión: una petición GET no cambia el estado de una sala.
- CP18 registro autorizado de No-Show.
- CP19 bloqueo temporal de tres días.
- CP20 rechazo de reservas durante el bloqueo.
- CP21 duración máxima de una hora, validada en formulario y backend.
- CP22 consulta de reportes e indicadores, añadido sin renumerar los casos existentes.

Los resultados se completan únicamente después de ejecutar cada caso. CP06 requiere una base PostgreSQL y solicitudes concurrentes; una prueba secuencial con SQLite no acredita concurrencia.
