# MEMORY — Reserva de Salas

## Proyecto
Sistema de Reserva de Salas para una Institución Educativa. El objetivo es reemplazar el proceso basado en correo electrónico y Excel por un sistema web para consultar disponibilidad y gestionar reservas.

## Actores
### Alumno
Inicia sesión, consulta disponibilidad, reserva directamente, cancela y consulta historial.

### Secretaría
Realiza reservas asistidas. Ingresa RUT y valida condición de alumno regular. Puede realizar acciones administrativas autorizadas, incluido No-Show.

### Administrador
Gestiona salas, usuarios/permisos según diseño, reportes y acciones administrativas autorizadas.

## Reglas de negocio
- RB01: alumnos pueden reservar directamente.
- RB02: reserva asistida debe validar RUT y alumno regular.
- RB03: reserva válida se confirma automáticamente.
- RB04: en concurrencia válida gana la primera solicitud procesada correctamente.
- RB05: máximo 2 reservas por alumno/día.
- RB06: no simultáneas ni consecutivas para el mismo alumno.
- RB07: asistentes <= capacidad de sala.
- RB08: cancelación >= 24 horas antes.
- RB09: sala ocupada no puede reservarse nuevamente.
- RB10: reserva confirmada que termina sin uso y sin cancelación previa puede registrarse como No-Show.
- RB11: No-Show aplica bloqueo de 3 días calendario.
- RB12: cada reserva individual puede durar como máximo 1 hora; las reservas confirmadas existentes no se cancelan automáticamente por este cambio.

## Requisitos funcionales
RF01 autenticación; RF02 validación de alumno regular; RF03 disponibilidad; RF04 datos de sala; RF05 crear reserva; RF06 conflictos; RF07 capacidad; RF08 máximo diario; RF09 solapamiento/consecutividad; RF10 cancelación; RF11 24 horas; RF12 historial; RF13 confirmación por correo; RF14 reportes; RF15 gestión de salas; RF16 usuarios/permisos; RF17 registro de No-Show; RF18 bloqueo temporal; RF19 duración máxima de 1 hora por reserva.

## Estados
Reserva: `CONFIRMADA`, `CANCELADA`, `NO_SHOW`.
Usuario: el bloqueo temporal es una restricción/atributo temporal y no un estado de la reserva.

## Seguridad y operación añadidas
- RF13 confirma por correo tras crear una reserva, si el alumno tiene una dirección válida.
- Contraseñas nuevas o cambiadas requieren mínimo 8 caracteres, mayúscula, minúscula, número y símbolo.
- django-axes registra fallos y bloquea la combinación de usuario/IP por 15 minutos tras 5 intentos.
- La confirmación por correo se envía después del commit si el alumno tiene una dirección válida.
- RF14 incorpora filtros por fecha/sala, estado, reservas por fecha/sala, bloqueos vigentes y duración reservada confirmada.
- El indicador de duración no es un porcentaje de ocupación: el proyecto no define horarios de disponibilidad de salas.

## Estado de la Implementación
Prototipo web completamente implementado con Django 4.2.x, Python 3.12 y Bootstrap 5.
- Base de datos relacional con modelos `User`, `Room`, `Reservation` y `AuditLog`.
- La creación normal de cuentas y salas se realiza desde los flujos administrativos. El comando opcional `bootstrap_initial_admin` solo crea el primer Administrador cuando `INITIAL_ADMIN_BOOTSTRAP=true`; no crea Alumno ni Secretaría y no modifica cuentas existentes.
- Suite de pruebas de unidad e integración disponible con `python manage.py test`.
