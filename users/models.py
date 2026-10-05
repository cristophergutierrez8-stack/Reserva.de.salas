from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    class Role(models.TextChoices):
        ALUMNO = 'ALUMNO', 'Alumno'
        SECRETARIA = 'SECRETARIA', 'Secretaría'
        ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'

    rut = models.CharField(
        max_length=12,
        unique=True,
        null=True,
        blank=True,
        help_text="RUT del usuario (ejemplo: 12345678-9)"
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ALUMNO,
        help_text="Rol asignado en el sistema"
    )
    is_regular_student = models.BooleanField(
        default=True,
        help_text="Indica si el alumno cuenta con condición de alumno regular"
    )
    blocked_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora hasta la cual el usuario está bloqueado temporalmente (3 días calendario)"
    )

    def is_alumno(self):
        return self.role == self.Role.ALUMNO or self.is_superuser

    def is_secretaria(self):
        return self.role == self.Role.SECRETARIA or self.is_superuser

    def is_administrador(self):
        return self.role == self.Role.ADMINISTRADOR or self.is_superuser

    def is_blocked(self):
        if self.blocked_until and timezone.now() < self.blocked_until:
            return True
        return False

    def apply_noshow_block(self):
        """Aplica un bloqueo temporal de 3 días calendario al usuario por No-Show."""
        now = timezone.now()
        # Si ya tenía un bloqueo futuro, extendemos 3 días desde ahora o desde la fecha actual
        self.blocked_until = now + timedelta(days=3)
        self.save(update_fields=['blocked_until'])

    def __str__(self):
        full_name = self.get_full_name()
        display = full_name if full_name else self.username
        if self.rut:
            return f"{display} ({self.rut}) - {self.get_role_display()}"
        return f"{display} - {self.get_role_display()}"
