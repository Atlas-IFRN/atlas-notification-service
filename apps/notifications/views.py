from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics, pagination
from rest_framework.views import APIView

from config.permissions import IsInternalService

from .models import AuditLog, Notification
from .serializers import AuditLogSerializer, InternalNotificationCreateSerializer, NotificationSerializer


class AuditLogPagination(pagination.PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 100


class AuditLogListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AuditLogSerializer
    pagination_class = AuditLogPagination

    def get_queryset(self):
        queryset = AuditLog.objects.all()
        action_name = self.request.query_params.get('action')
        if action_name:
            queryset = queryset.filter(action=action_name.upper())
        return queryset


class NotificationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Janela deslizante configurável (padrão 5 dias), recalculada a cada
        # request. As NÃO lidas ficam sempre visíveis, independentemente da
        # idade — a janela só oculta o que já foi lido, para que nada marcado
        # "pra ler depois" desapareça silenciosamente.
        window_days = getattr(settings, 'NOTIFICATION_LIST_WINDOW_DAYS', 5)
        window_start = timezone.now() - timedelta(days=window_days)
        qs = Notification.objects.filter(user_id=request.user.id).filter(
            Q(is_read=False) | Q(created_at__gte=window_start)
        )

        is_read = request.query_params.get('is_read')
        if is_read is not None:
            qs = qs.filter(is_read=is_read.lower() in ('true', '1', 'yes'))

        type_filter = request.query_params.get('type')
        if type_filter:
            qs = qs.filter(type=type_filter)

        qs = qs.order_by('-created_at')

        paginator = NotificationPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = NotificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class NotificationReadView(APIView):
    """PATCH /notifications/{id}/read/ — marca uma notificação como lida."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id):
        notif = get_object_or_404(Notification, pk=notification_id, user_id=request.user.id)
        if not notif.is_read:
            notif.is_read = True
            notif.save(update_fields=['is_read'])
        return Response(NotificationSerializer(notif).data, status=status.HTTP_200_OK)


class NotificationMarkAllReadView(APIView):
    """POST /notifications/mark-all-read/ — marca todas as não lidas como lidas."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        notifications = list(
            Notification.objects.filter(user_id=request.user.id, is_read=False)
        )
        for notification in notifications:
            notification.is_read = True
            notification.save(update_fields=['is_read'])
        updated = len(notifications)
        return Response({"updated": updated}, status=status.HTTP_200_OK)


class InternalNotificationCreateView(APIView):
    """POST /internal/notifications/ — criação serviço-a-serviço.

    Chamada por outros serviços (auth, scholarship, tracks...) diretamente pela
    rede Docker, protegida pelo segredo compartilhado no header X-Internal-Token.
    Não passa pela barreira de JWT do gateway.
    """

    authentication_classes = []
    permission_classes = [IsInternalService]

    def post(self, request):
        serializer = InternalNotificationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
