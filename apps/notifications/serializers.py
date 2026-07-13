from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'is_read', 'type', 'link', 'created_at']


class InternalNotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer da rota interna de criação (serviço-a-serviço).

    Aceita um `event_id` opcional para idempotência: reenvios com a mesma chave
    reaproveitam a notificação existente em vez de duplicar (mesma garantia do
    caminho por fila).
    """

    class Meta:
        model = Notification
        fields = ['id', 'user_id', 'title', 'message', 'type', 'link', 'event_id', 'is_read', 'created_at']
        read_only_fields = ['id', 'is_read', 'created_at']
        # `validators: []` remove o UniqueValidator que o DRF adiciona sozinho
        # por `event_id` ser unique — senão um reenvio com a mesma chave falharia
        # com 400 na validação, antes do get_or_create idempotente do create().
        extra_kwargs = {'event_id': {'required': False, 'validators': []}}

    def create(self, validated_data):
        event_id = validated_data.get('event_id')
        if event_id:
            notification, _ = Notification.objects.get_or_create(
                event_id=event_id,
                defaults=validated_data,
            )
            return notification
        return super().create(validated_data)
