from django.db import models


class Room(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre de la Sala"
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Código de la Sala"
    )
    capacity = models.PositiveIntegerField(
        verbose_name="Capacidad Máxima de Asistentes"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descripción / Equipamiento"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activa / Disponible para Reservas"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']
        verbose_name = "Sala"
        verbose_name_plural = "Salas"

    def __str__(self):
        return f"{self.name} ({self.code}) - Capacidad: {self.capacity} pers."
