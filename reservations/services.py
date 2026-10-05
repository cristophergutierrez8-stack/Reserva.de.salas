from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from reservations.models import Reservation
from audit.models import AuditLog


def validate_and_create_reservation(student, created_by, room, date, start_time, end_time, attendees_count):
    """
    Valida todas las reglas de negocio en backend y crea una reserva de forma atómica.
    """
    # 1. Validación de Bloqueo Temporal (3 días por No-Show)
    if student.is_blocked():
        blocked_str = student.blocked_until.strftime('%d/%m/%Y a las %H:%M')
        raise ValidationError(f"El alumno tiene un bloqueo vigente hasta {blocked_str}.")

    # 2. Estado de la Sala
    if not room.is_active:
        raise ValidationError("La sala seleccionada no se encuentra activa para reservas.")

    # 3. Validación de Fechas y Horarios válidos
    now = timezone.now()
    today = now.date()
    if date < today:
        raise ValidationError("No se pueden realizar reservas para fechas pasadas.")

    if start_time >= end_time:
        raise ValidationError("La hora de inicio debe ser anterior a la hora de término.")

    # Si la reserva es para hoy, validar que la hora de inicio no haya pasado
    start_dt = timezone.make_aware(datetime.combine(date, start_time))
    if date == today and start_dt < now:
        raise ValidationError("La hora de inicio seleccionada ya ha transcurrido.")

    # 4. Capacidad de la Sala (RB07)
    if attendees_count <= 0:
        raise ValidationError("Debe indicar al menos 1 asistente.")
    if attendees_count > room.capacity:
        raise ValidationError(f"La sala no tiene capacidad suficiente (Capacidad máxima: {room.capacity}).")

    # Transacción atómica y control de concurrencia
    with transaction.atomic():
        # Bloqueo a nivel de filas para prevenir condiciones de carrera simultáneas
        # 5. Límite diario de 2 reservas por alumno (RB05)
        existing_today_count = Reservation.objects.select_for_update().filter(
            student=student,
            date=date,
            status=Reservation.Status.CONFIRMADA
        ).count()

        if existing_today_count >= 2:
            raise ValidationError("El alumno ya tiene 2 reservas para este día.")

        # 6. Conflicto de Sala (RB04/RB09) - Sala ya reservada en ese horario
        room_conflict = Reservation.objects.select_for_update().filter(
            room=room,
            date=date,
            status=Reservation.Status.CONFIRMADA,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()

        if room_conflict:
            raise ValidationError("La sala ya fue reservada para ese horario.")

        # 7. Solapamiento de Horario del Alumno (RB06) - Mismo alumno en salas distintas
        student_conflict = Reservation.objects.select_for_update().filter(
            student=student,
            date=date,
            status=Reservation.Status.CONFIRMADA,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()

        if student_conflict:
            raise ValidationError("El alumno ya posee una reserva superpuesta en ese horario.")

        # 8. Reservas Consecutivas del Alumno (RB06/RB13) - Mismo alumno termina/empieza justo al mismo tiempo
        consecutive_conflict = Reservation.objects.select_for_update().filter(
            student=student,
            date=date,
            status=Reservation.Status.CONFIRMADA
        ).filter(
            models_q_consecutive(start_time, end_time)
        ).exists()

        if consecutive_conflict:
            raise ValidationError("No se permiten reservas consecutivas.")

        # Crear reserva confirmada
        reservation = Reservation.objects.create(
            student=student,
            created_by=created_by,
            room=room,
            date=date,
            start_time=start_time,
            end_time=end_time,
            attendees_count=attendees_count,
            status=Reservation.Status.CONFIRMADA
        )

        # Registrar auditoría si fue reserva asistida por Secretaría
        if created_by != student:
            AuditLog.objects.create(
                user=created_by,
                action="Reserva Asistida Creada",
                entity_affected=f"Reserva #{reservation.pk}",
                details=f"Secretaría creó reserva para Alumno {student.username} (RUT: {student.rut}) en sala {room.code}"
            )

        return reservation


def models_q_consecutive(start_time, end_time):
    from django.db.models import Q
    return Q(end_time=start_time) | Q(start_time=end_time)


def cancel_reservation(reservation, user):
    """
    Cancela una reserva verificando la regla de 24 horas y permisos.
    """
    if reservation.status != Reservation.Status.CONFIRMADA:
        raise ValidationError("Solo se pueden cancelar reservas en estado Confirmada.")

    # Verificar permisos (Alumno dueño, Secretaría o Administrador)
    if not (user == reservation.student or user.is_secretaria() or user.is_administrador()):
        raise ValidationError("No tiene permisos para cancelar esta reserva.")

    # Regla de 24 horas (RB08)
    if not reservation.can_be_cancelled():
        raise ValidationError("La reserva no puede cancelarse porque faltan menos de 24 horas.")

    with transaction.atomic():
        reservation.status = Reservation.Status.CANCELADA
        reservation.save(update_fields=['status', 'updated_at'])

        AuditLog.objects.create(
            user=user,
            action="Reserva Cancelada",
            entity_affected=f"Reserva #{reservation.pk}",
            details=f"Usuario {user.username} canceló la reserva para la sala {reservation.room.code}"
        )

    return reservation


def register_noshow(reservation, registered_by_user):
    """
    Registra No-Show en una reserva terminada y aplica el bloqueo de 3 días al alumno.
    Solo personal autorizado (Secretaría / Administrador).
    """
    if not (registered_by_user.is_secretaria() or registered_by_user.is_administrador()):
        raise ValidationError("No tiene autorización para registrar No-Show.")

    if not reservation.can_be_marked_noshow():
        raise ValidationError("Solo se puede registrar No-Show en reservas confirmadas que ya hayan finalizado.")

    with transaction.atomic():
        # Actualizar estado de la reserva
        reservation.status = Reservation.Status.NO_SHOW
        reservation.noshow_registered_by = registered_by_user
        reservation.noshow_registered_at = timezone.now()
        reservation.save(update_fields=['status', 'noshow_registered_by', 'noshow_registered_at', 'updated_at'])

        # Aplicar restricción temporal de 3 días al alumno
        reservation.student.apply_noshow_block()

        AuditLog.objects.create(
            user=registered_by_user,
            action="Registro No-Show",
            entity_affected=f"Reserva #{reservation.pk} (Alumno {reservation.student.username})",
            details=f"No-Show registrado. Bloqueo de 3 días aplicado al alumno {reservation.student.username} hasta {reservation.student.blocked_until}"
        )

    return reservation
