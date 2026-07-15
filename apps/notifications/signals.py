from django.db.models.signals import post_delete, post_save, pre_save

from .audit import get_current_actor_id, snapshot_instance
from .models import AuditAction, AuditLog, Notification


def capture_before_save(sender, instance, **kwargs):
    instance._audit_before = None
    if instance.pk:
        previous = sender._default_manager.filter(pk=instance.pk).first()
        if previous is not None:
            instance._audit_before = snapshot_instance(previous)


def _write_log(instance, action, payload):
    AuditLog.objects.create(
        table_name='notification',
        action=action,
        record_id=instance.pk,
        user_id=get_current_actor_id(),
        payload=payload,
    )


def audit_after_save(sender, instance, created, **kwargs):
    after = snapshot_instance(instance)
    if created:
        _write_log(instance, AuditAction.CREATE, {'after': after})
    else:
        _write_log(
            instance,
            AuditAction.UPDATE,
            {'before': getattr(instance, '_audit_before', None), 'after': after},
        )


def audit_after_delete(sender, instance, **kwargs):
    _write_log(instance, AuditAction.DELETE, {'before': snapshot_instance(instance)})


pre_save.connect(
    capture_before_save,
    sender=Notification,
    dispatch_uid='notifications_audit_pre_save',
)
post_save.connect(
    audit_after_save,
    sender=Notification,
    dispatch_uid='notifications_audit_post_save',
)
post_delete.connect(
    audit_after_delete,
    sender=Notification,
    dispatch_uid='notifications_audit_post_delete',
)
