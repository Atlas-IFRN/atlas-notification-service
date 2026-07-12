from django.urls import path

from .views import InternalNotificationCreateView

urlpatterns = [
    path('notifications/', InternalNotificationCreateView.as_view(), name='internal_notification_create'),
]
