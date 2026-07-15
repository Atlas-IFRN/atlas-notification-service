import json
from contextvars import ContextVar

from django.core.serializers.json import DjangoJSONEncoder


_current_actor_id = ContextVar('notification_audit_actor_id', default=None)


def set_current_actor_id(user_id):
    _current_actor_id.set(str(user_id) if user_id else None)


def clear_current_actor_id():
    _current_actor_id.set(None)


def get_current_actor_id():
    return _current_actor_id.get()


def snapshot_instance(instance):
    data = {}
    for field in instance._meta.concrete_fields:
        value = getattr(instance, field.attname, None)
        data[field.name] = value
    return json.loads(json.dumps(data, cls=DjangoJSONEncoder))
