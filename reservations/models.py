from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from rooms.models import Room


class Reservation(models.Model):
    class Status(models.TextChoices):
        CONFIRMADA = 'CONFIRMADA', 'Confirmada'
        CANCELADA = 'CANCELADA', 'Cancelada'
        NO_SHOW = 'NO_SHOW', 'No-Show'

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name="Alumno Beneficiario"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_reservations',
        verbose_name="Usuario Creador (Alumno / Secretaría)"
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name="Sala"
    )
    date = models.DateField(
        verbose_name="Fecha de Reserva"
    )
    start_time = models.TimeField(
        verbose_name="Hora Inicio"
    )
    end_time = models.TimeField(
        verbose_name="Hora Término"
    )
    attendees_count = models.PositiveIntegerField(
        verbose_name="Cantidad de Asistentes"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMADA,
        verbose_name="Estado de la Reserva"
    )

    # Datos de auditoría de No-Show
    noshow_registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registered_noshows',
        verbose_name="No-Show Registrado Por"
    )
    noshow_registered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha/Hora Registro No-Show"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-start_time']
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"

    @property
    def start_datetime(self):
        return timezone.make_aware(datetime.combine(self.date, self.start_time))

    @property
    def end_datetime(self):
        return timezone.make_aware(datetime.combine(self.date, self.end_time))

    def can_be_cancelled(self):
        """Una reserva confirmada solo se puede cancelar con al menos 24 horas de anticipación."""
        if self.status != self.Status.CONFIRMADA:
            return False
        now = timezone.now()
        return (self.start_datetime - now) >= timedelta(hours=24)

    def can_be_marked_noshow(self):
        """
        Una reserva confirmada solo puede convertirse en No-Show cuando:
        - finalizó su horario (end_datetime < now)
        - no fue cancelada previa ni marcada antes como No-Show
        """
        if self.status != self.Status.CONFIRMADA:
            return False
        return self.end_datetime < timezone.now()

    def __str__(self):
        return f"Reserva #{self.pk} - {self.room.code} - {self.date} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')} ({self.student.username})"
