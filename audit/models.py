from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name="Usuario Ejecutor"
    )
    action = models.CharField(
        max_length=255,
        verbose_name="Acción Realizada"
    )
    entity_affected = models.CharField(
        max_length=255,
        verbose_name="Entidad / Recurso Afectado"
    )
    details = models.TextField(
        blank=True,
        verbose_name="Detalles / Metadatos"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Dirección IP"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y Hora"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Registros de Auditoría"

    def __str__(self):
        user_str = self.user.username if self.user else "Sistema/Anónimo"
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {user_str} - {self.action} ({self.entity_affected})"
