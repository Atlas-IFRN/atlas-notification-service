"""
Task Celery de criação de notificações.

Este serviço é o dono do consumo: o worker escuta a fila `notifications` e grava
as notificações no banco. Os produtores (auth, scholarship, tracks...) publicam
o evento pelo NOME `notifications.create` via `send_task`, sem importar este
módulo — o acoplamento é só o nome da task + a fila no RabbitMQ.
"""
import logging

from celery import shared_task

from .models import Notification, NotificationType

logger = logging.getLogger(__name__)


@shared_task(
    name="notifications.create",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    acks_late=True,
)
def create_notification(self, user_id, title, message, type="system", event_id=None):
    """Persiste uma notificação a partir de um evento publicado na fila.

    Idempotente: se `event_id` vier preenchido, uma reentrega do broker
    (acks_late) reaproveita a notificação já criada em vez de duplicar.

    Erros de *contrato* (campos obrigatórios ausentes, tipo inválido) não são
    retentáveis — retry não muda o resultado, então logamos e encerramos.
    Só falhas *transitórias* (banco indisponível, etc.) reenfileiram.
    """
    # --- validação do contrato do evento (não-retentável) --------------------
    if not user_id or not title or not message:
        logger.error(
            "Evento notifications.create descartado (campos obrigatórios ausentes): "
            "user_id=%s title=%r message_vazio=%s",
            user_id, title, not bool(message),
        )
        return None

    if type not in NotificationType.values:
        logger.warning(
            "Tipo '%s' desconhecido no evento para %s — assumindo SYSTEM.", type, user_id
        )
        type = NotificationType.SYSTEM

    # --- persistência (falha aqui é transitória → retry) ---------------------
    try:
        if event_id:
            notification, created = Notification.objects.get_or_create(
                event_id=event_id,
                defaults={
                    "user_id": user_id,
                    "title": title,
                    "message": message,
                    "type": type,
                },
            )
            if not created:
                logger.info(
                    "Evento %s já processado (notificação %s) — reentrega ignorada.",
                    event_id, notification.id,
                )
                return str(notification.id)
        else:
            notification = Notification.objects.create(
                user_id=user_id,
                title=title,
                message=message,
                type=type,
            )
    except Exception as exc:
        logger.exception("Falha ao criar notificação para o usuário %s — reenfileirando.", user_id)
        raise self.retry(exc=exc)

    logger.info("Notificação %s criada para o usuário %s (%s).", notification.id, user_id, type)
    return str(notification.id)
