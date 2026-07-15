import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class NotificationType(models.TextChoices):
    # O valor é usado pelo frontend para escolher o ícone da notificação.
    FEED_LIKE = 'feed_like', _('Feed like')
    FEED_COMMENT = 'feed_comment', _('Feed comment')
    TRACK = 'track', _('Track')
    SCHOLARSHIP = 'scholarship', _('Scholarship')
    SYSTEM = 'system', _('System')


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # O usuário vive no schema do auth-service; aqui guardamos apenas o UUID
    # (sem FK entre schemas/serviços).
    user_id = models.UUIDField(db_index=True)

    # Chave de idempotência do evento. O produtor gera um UUID por evento; se o
    # broker reentregar a mensagem (acks_late + falha após persistir), o UNIQUE
    # deduplica em vez de gravar a mesma notificação duas vezes. Nulo quando o
    # produtor não envia chave (comportamento best-effort legado).
    event_id = models.UUIDField(null=True, blank=True, unique=True, db_index=True)

    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    type = models.CharField(max_length=20, choices=NotificationType.choices)

    # Rota relativa do frontend para abrir o item relacionado ao clicar na
    # notificação (ex.: "/inicio/post/<uuid>"). Vazio = notificação sem
    # deep-link (só marca como lida no clique). Quem preenche é o produtor.
    link = models.CharField(max_length=500, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.type}] {self.title} ({self.user_id})"


class AuditAction(models.TextChoices):
    CREATE = 'CREATE', _('Create')
    UPDATE = 'UPDATE', _('Update')
    DELETE = 'DELETE', _('Delete')


class AuditLogTable(models.TextChoices):
    NOTIFICATION = 'notification', _('Notification')


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    table_name = models.CharField(max_length=100, choices=AuditLogTable.choices)
    action = models.CharField(max_length=10, choices=AuditAction.choices)
    record_id = models.UUIDField(help_text='PK do registro afetado')
    user_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text='UUID do usuário responsável pela operação',
    )
    payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['user_id', '-created_at'], name='notif_audit_user_time_idx'),
            models.Index(fields=['-created_at'], name='notif_audit_created_idx'),
        ]

    def __str__(self):
        return f'[{self.action}] {self.table_name} ({self.record_id})'
