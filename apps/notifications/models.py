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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.type}] {self.title} ({self.user_id})"
