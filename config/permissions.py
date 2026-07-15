from django.conf import settings
from rest_framework.permissions import BasePermission


class IsTeacher(BasePermission):
    """Permite acesso somente a usuários autenticados com papel de professor."""

    message = "Apenas professores podem acessar este recurso."

    def has_permission(self, request, view):
        user = request.user
        role = str(getattr(user, "role", "") or "").upper()
        return bool(user and user.is_authenticated and role == "TEACHER")


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
