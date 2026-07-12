from django.conf import settings
from rest_framework.permissions import BasePermission


class IsInternalService(BasePermission):
    """
    Libera o acesso apenas para chamadas serviço-a-serviço que apresentem o
    segredo compartilhado no header `X-Internal-Token`.

    Usada na rota interna de criação de notificações, chamada por outros
    serviços (auth, scholarship, tracks...) diretamente pela rede Docker —
    sem passar pela barreira de JWT do gateway.
    """

    message = "Token interno ausente ou inválido."

    def has_permission(self, request, view):
        expected = getattr(settings, "INTERNAL_TOKEN", "") or ""
        provided = request.headers.get("X-Internal-Token", "")
        # Sem segredo configurado, nega por segurança (fail-closed).
        return bool(expected) and provided == expected
