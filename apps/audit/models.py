from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        null=True,
        blank=True,
    )
    actor_email = models.EmailField(blank=True, default="")
    action = models.CharField(max_length=160)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    status_code = models.PositiveSmallIntegerField()
    resource_type = models.CharField(max_length=100, blank=True, default="")
    resource_id = models.CharField(max_length=100, blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True, default="")
    request_id = models.CharField(max_length=100, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Audit log")
        verbose_name_plural = _("Audit logs")
        indexes = [
            models.Index(
                fields=["resource_type", "resource_id"],
                name="audit_resource_idx",
            ),
            models.Index(
                fields=["actor_email", "created_at"],
                name="audit_actor_time_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Audit logs are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Audit logs cannot be deleted.")

    def __str__(self):
        return f"{self.method} {self.path} [{self.status_code}]"

