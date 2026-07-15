# Atlas · Notification Service 🔔

> Parte do **Projeto Atlas** — plataforma acadêmica desenvolvida para o **IFRN Campus Pau dos Ferros** como Projeto Integrador de Sistemas Distribuídos. O Atlas conecta alunos a trilhas de conhecimento e bolsas, com avaliação automática de código por IA.

Microsserviço responsável pelas **notificações** da plataforma. É o **consumidor central**: os demais serviços publicam eventos no RabbitMQ e este serviço os transforma em notificações persistidas e consultáveis pelo usuário.

## O que este serviço faz

- **Consumo assíncrono:** um **worker Celery dedicado** (`celery-worker-notifications`, fila `notifications`) escuta o evento `notifications.create` publicado por auth, feed, tracks e scholarship.
- **Persistência tipada:** grava `Notification` com tipo (`NotificationType`), destinatário e link/deeplink.
- **Consulta e leitura:** o usuário lista suas notificações, marca uma como lida ou marca todas como lidas.
- **Auditoria:** modelo `AuditLog` com registro automático e endpoint de consulta.

## Stack

- Python · Django · Django REST Framework
- PostgreSQL 16 (schema `notification`) · Redis · RabbitMQ + Celery (consumidor)
- Gunicorn · Docker · drf-spectacular (Swagger)

## Como se encaixa no Atlas

| Repositório | Responsabilidade |
|---|---|
| atlas-auth-service | Identidade: SUAP OAuth2, JWT, perfis de usuário |
| atlas-track-service | Trilhas, módulos, conteúdos, progresso e submissão de desafios |
| atlas-scholarship-service | Bolsas, candidaturas, banco de talentos e notas |
| atlas-feed-service | Feed institucional: posts, comentários, curtidas e banners |
| **atlas-notification-service** | **Notificações (consumidor central via RabbitMQ)** |
| atlas-ai-service | Avaliação de repositórios GitHub por LLM local (Ollama) |
| atlas-frontend | SPA React + TypeScript (aluno e professor) |
| atlas-infra | Docker Compose, Nginx (gateway), Postgres/Redis/RabbitMQ, deploy e backup |
| atlas-observability | Prometheus + Grafana (métricas dos serviços) |

**Padrão pub/sub:** os produtores publicam eventos *best-effort* (se o broker estiver fora, a ação principal não é bloqueada). Este serviço é o único **consumidor** — concentrando a lógica de notificação em um só lugar.

## Domínio (models principais)

`Notification` (com `NotificationType`) · `AuditLog`

## Principais endpoints (`/api/notifications/`)

`notifications/` · `notifications/<id>/read/` · `notifications/mark-all-read/` · `audit-logs/`. Documentação em `api/notifications/docs/`.

## Estrutura

```
apps/notifications/   models, views, serializers, services, tasks (consumo), audit
config/               settings (base/local/production), urls, celery, authentication, permissions
```

## Executando localmente

> Orquestrado pelo repositório central: **[Atlas-IFRN/atlas-infra](https://github.com/Atlas-IFRN/atlas-infra)**.

```bash
git clone https://github.com/Atlas-IFRN/atlas-infra
cd atlas-infra && docker compose -f docker-compose.dev.yml up -d

cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000

# Worker consumidor (obrigatório para processar eventos)
celery -A config worker -l info -Q notifications
```

## Variáveis de ambiente

Baseie seu `.env` no `.env.example`. Principais: `DJANGO_SECRET_KEY` (compartilhada — valida o JWT), `DATABASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`, `AUTH_SERVICE_URL`.

## Observabilidade & Auditoria

- **Métricas:** `/metrics` (django-prometheus), coletado pelo [atlas-observability](https://github.com/Atlas-IFRN/atlas-observability).
- **Auditoria:** `AuditLog` registra operações com `user_id` e timestamp, consultáveis em `audit-logs/`.

## CI/CD

Workflows de GitHub Actions em `.github/workflows/`.
