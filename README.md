# Notification Service 🔔

Microserviço do ecossistema **Atlas** responsável pelo gerenciamento das
notificações dos usuários (boas-vindas, avaliações, bolsas e avisos de sistema).

Foi extraído do `auth-service` para isolar o domínio de notificações em seu
próprio serviço e schema de banco (`notification`).

## Stack

- Python · Django 6.x · Django REST Framework
- PostgreSQL (schema `notification`)
- Celery + RabbitMQ (consumo de eventos)
- Docker · drf-spectacular (Swagger/OpenAPI 3.0)

## Arquitetura

- **Autenticação:** stateless via JWT no header `Authorization`, validado
  localmente com a mesma `DJANGO_SECRET_KEY` compartilhada entre os serviços
  (nenhuma chamada de rede ao auth-service). Ver `config/authentication.py`.
- **Sem FK para User:** como o usuário vive no schema do `auth-service`, a
  notificação guarda apenas o `user_id` (UUID) — não há chave estrangeira
  entre schemas.
- **Event-driven (caminho principal):** este serviço é o **dono do consumo**.
  Um worker Celery (`celery-worker-notifications`) escuta a fila `notifications`
  no RabbitMQ e persiste as notificações. Os produtores (auth, scholarship,
  tracks...) apenas **publicam** o evento pelo nome `notifications.create` via
  `send_task` — sem HTTP e sem importar o código da task. Isso desacopla os
  produtores da disponibilidade deste serviço e dá retry/durabilidade pela fila.

  ```python
  # exemplo no produtor (só precisa do broker + nome da task + fila):
  celery_app.send_task(
      "notifications.create",
      kwargs={
          "user_id": str(uid), "title": "...", "message": "...", "type": "SYSTEM",
          "event_id": str(uuid.uuid4()),  # opcional, mas recomendado (idempotência)
      },
      queue="notifications",
  )
  ```
- **Idempotência:** com `acks_late`, o broker pode reentregar uma mensagem já
  processada. Envie um `event_id` (UUID) único por evento e o serviço deduplica
  (constraint UNIQUE + `get_or_create`) em vez de gravar a notificação duas
  vezes. Sem `event_id`, o comportamento é best-effort (sem dedup), como antes.
- **Criação interna via HTTP (fallback):** também há
  `POST /api/notifications/internal/notifications/`, protegido pelo header
  `X-Internal-Token` (segredo `INTERNAL_TOKEN`), para casos síncronos ou serviços
  sem Celery (ex.: o `ai-service`, em FastAPI) e para debug/testes.

## Executando localmente

Este serviço é orquestrado junto com todos os outros pelo repositório central de
infraestrutura:

> **[Atlas-IFRN/atlas-infra](https://github.com/Atlas-IFRN/atlas-infra)** — Docker Compose canônico, Nginx, scripts de deploy e backup.

Para subir apenas a infraestrutura compartilhada (Postgres, Redis, RabbitMQ) e
rodar este serviço isolado em modo dev:

```bash
# 1. Suba a infra compartilhada
git clone https://github.com/Atlas-IFRN/atlas-infra
cd atlas-infra
docker compose -f docker-compose.dev.yml up -d

# 2. Neste repositório
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8004
```

## Variáveis de ambiente

Crie um `.env` baseado no `.env.example`. Principais: `DATABASE_URL`,
`DJANGO_SECRET_KEY`, `INTERNAL_TOKEN`.

## Documentação da API

Com o serviço rodando, acesse a documentação interativa:

- **Swagger UI:** `http://localhost:8000/api/notifications/docs/`

## Endpoints

Todos os endpoints públicos exigem o header `Authorization: Bearer <token>`.

### Listar notificações do usuário autenticado

`GET /api/notifications/notifications/`

Retorna as notificações **não lidas (sempre)** mais as **lidas** dentro da janela
de `NOTIFICATION_LIST_WINDOW_DAYS` dias (padrão 5) — assim nada marcado "pra ler
depois" desaparece. Resposta **paginada** (`page_size` padrão 20, até 100).

Filtros/opções via query string: `?is_read=true|false`,
`?type=SCHOLARSHIP|EVALUATION|SYSTEM`, `?page=N` e `?page_size=N`.

### Marcar uma notificação como lida

`PATCH /api/notifications/notifications/<uuid>/read/`

### Marcar todas como lidas

`POST /api/notifications/notifications/mark-all-read/`

### Criar notificação (uso interno — serviço-a-serviço)

`POST /api/notifications/internal/notifications/`

Header obrigatório: `X-Internal-Token: <INTERNAL_TOKEN>`.

```json
{
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "title": "Bem-vindo ao ATLAS! 🎓",
  "message": "Sua conta foi criada com sucesso.",
  "type": "SYSTEM",
  "event_id": "9f1c2b3a-0000-4a5b-8c6d-1e2f3a4b5c6d"
}
```

O campo `event_id` (UUID) é opcional e garante idempotência: reenvios com a
mesma chave reaproveitam a notificação existente em vez de duplicar.
