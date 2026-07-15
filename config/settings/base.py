"""
Configurações base — comuns a todos os ambientes.
"""
import os
from pathlib import Path

import environ

# ------------------------------------------------------------------------------
# PATHS
# ------------------------------------------------------------------------------
# config/settings/base.py -> config/settings -> config -> <project_root>
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ------------------------------------------------------------------------------
# ENVIRONMENT VARIABLES
# ------------------------------------------------------------------------------
env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# ------------------------------------------------------------------------------
# CORE
# ------------------------------------------------------------------------------
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="django-insecure-p6^ped7h!8lxdm0f7pw%u0p!$h--b6lpi7aae5eli4(g)a+u@6"
)

DEBUG = env.bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

# Segredo compartilhado para chamadas internas serviço-a-serviço
# (criação de notificações a partir de outros serviços).
INTERNAL_TOKEN = env("INTERNAL_TOKEN", default="")

# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================

DATABASES = {
    # O método env.db() lê a variável DATABASE_URL do seu .env.
    # Se ela não existir, ele usa o SQLite como fallback (valor padrão).
    'default': env.db(
        'DATABASE_URL',
        default=f'sqlite:///{BASE_DIR}/db.sqlite3'
    )
}

# ------------------------------------------------------------------------------
# APPS
# ------------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'rest_framework',

    # Local apps
    "apps.notifications",

    # biblioteca responsável por gerar a documentação Swagger da API
    'drf_spectacular',

    # Exporta métricas em /metrics para o Prometheus (atlas-observability).
    'django_prometheus',
]

# ------------------------------------------------------------------------------
# MIDDLEWARE
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    # django-prometheus: PRIMEIRO middleware (mede a request inteira).
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.notifications.middleware.AuditActorMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # django-prometheus: ÚLTIMO middleware.
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "config.urls"

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    'DEFAULT_AUTHENTICATION_CLASSES': [
        'config.authentication.AtlasJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}

# Janela (em dias) do endpoint de listagem: notificações LIDAS mais antigas que
# isso são ocultadas; as não lidas permanecem sempre visíveis. Configurável por
# ambiente sem tocar no código.
NOTIFICATION_LIST_WINDOW_DAYS = env.int("NOTIFICATION_LIST_WINDOW_DAYS", default=5)

# ------------------------------------------------------------------------------
# SIMPLE JWT
# ------------------------------------------------------------------------------
# Validação local do token pelo header, sem chamar o auth-service.
#
# Chave de assinatura: por padrão usa a SECRET_KEY (que hoje é compartilhada
# entre os serviços via DJANGO_SECRET_KEY). Para separar o segredo de assinatura
# do JWT do SECRET_KEY do Django, defina JWT_SIGNING_KEY no .env — MAS ele
# precisa ser o MESMO valor no auth-service (que assina) e em TODOS os serviços
# que validam (track, scholarship, notification); do contrário os tokens deixam
# de ser aceitos. Enquanto não definido, o comportamento é idêntico ao anterior.
JWT_SIGNING_KEY = env("JWT_SIGNING_KEY", default=SECRET_KEY)

SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('Bearer',),
    'TOKEN_USER_CLASS': 'config.authentication.AtlasTokenUser',
    'SIGNING_KEY': JWT_SIGNING_KEY,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Notification Service API',
    'DESCRIPTION': 'Microsserviço responsável pela gestão de notificações dos usuários.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# ------------------------------------------------------------------------------
# TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ------------------------------------------------------------------------------
# PASSWORD VALIDATION
# ------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------------------------
# INTERNATIONALIZATION
# ------------------------------------------------------------------------------
LANGUAGE_CODE = "pt-br"

TIME_ZONE = "America/Sao_Paulo"

USE_I18N = True

USE_TZ = True

# ------------------------------------------------------------------------------
# STATIC FILES
# ------------------------------------------------------------------------------
STATIC_URL = "/api/notifications/static/"

# ------------------------------------------------------------------------------
# DEFAULTS
# ------------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================================================================
# CELERY (RabbitMQ broker)
# ==============================================================================
# O notification-service é dono do consumo: um worker Celery escuta a fila
# NOTIFICATIONS_QUEUE e grava as notificações no banco. Os serviços produtores
# (auth, scholarship, tracks...) apenas publicam o evento `notifications.create`
# nessa fila via send_task — sem HTTP e sem compartilhar o código da task.
NOTIFICATIONS_QUEUE = env("NOTIFICATIONS_QUEUE", default="notifications")

CELERY_BROKER_URL = env(
    'CELERY_BROKER_URL',
    default='amqp://guest:guest@rabbitmq:5672//',
)
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='rpc://')
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Roteia a task de criação para a fila dedicada (evita colidir com a fila
# default consumida pelo worker do tracks, que compartilha o mesmo RabbitMQ).
CELERY_TASK_ROUTES = {
    'notifications.create': {'queue': NOTIFICATIONS_QUEUE},
}
