from django.urls import path

from .views import (
    AuditLogListView,
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationReadView,
)

urlpatterns = [
    path('audit-logs/', AuditLogListView.as_view(), name='audit-log-list'),
    path('notifications/', NotificationListView.as_view(), name='notification_list'),
    path('notifications/<uuid:notification_id>/read/', NotificationReadView.as_view(), name='notification_read'),
    path('notifications/mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification_mark_all_read'),
]
