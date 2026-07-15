from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def health_check(request):
    return HttpResponse("OK", status=200)


urlpatterns = [
    path('api/notifications/admin/', admin.site.urls),
    path('health/', health_check),

    # Endpoint /metrics para o Prometheus (django-prometheus).
    path('', include('django_prometheus.urls')),

    # Rotas internas (serviço-a-serviço, protegidas por X-Internal-Token)
    path('api/notifications/internal/', include('apps.notifications.internal_urls')),

    # Rotas públicas (exigem JWT)
    path('api/notifications/', include('apps.notifications.urls')),

    path('api/notifications/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/notifications/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
