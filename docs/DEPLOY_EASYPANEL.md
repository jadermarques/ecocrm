# Deploy no Easypanel

Guia para implementar o ECOCRM no Easypanel com separação de serviços.

## Passo 1: Criar Services do tipo "App"

Para cada componente abaixo, crie um novo serviço no seu Projeto Easypanel.

### Service 1: `platform_api`
- **Source**: GitHub Repository
- **Dockerfile Path**: `Dockerfile.platform_api`
- **Port**: 8000
- **Environment**: Copie o conteúdo de `env/platform_api.env`.
  - *Ajuste* `DATABASE_URL` e `REDIS_URL` para apontar para os serviços de banco do Easypanel (ex: `postgres://...` e `redis://...`).
- **Mounts**: 
  - `/app/data` (Persistente para uploads)

### Service 2: `streamlit_portal`
- **Source**: GitHub Repository
- **Dockerfile Path**: `Dockerfile.streamlit_portal`
- **Port**: 8501
- **Environment**: Copie o conteúdo de `env/streamlit_portal.env`.
  - *Importante*: `PLATFORM_API_BASE_URL` deve ser o URL interno do serviço `platform_api` (ex: `http://platform_api:8000`).
  - Defina `PUBLIC_BASE_URL` com o domínio final.

### Service 3: `bot_runner` (Worker)
- **Source**: GitHub Repository
- **Dockerfile Path**: `Dockerfile.bot_runner`
- **Environment**: Copie o conteúdo de `env/bot_runner.env`.
  - *Importante*: Preencha `CHATWOOT_BASE_URL` com o endereço do seu Chatwoot.
- **Advanced**: Em "Deploy", desative exposição HTTP (não precisa de domínio).

### Service 4: `events_router` (Opcional/Futuro)
- **Source**: GitHub Repository
- **Dockerfile Path**: `bot_runner/Dockerfile` (Usa o mesmo código)
- **Environment**: Copie o conteúdo de `env/events_router.env`.
  - Garante que `WORKER_MODE=router`.

## Passo 2: Bancos de Dados

Crie serviços do tipo Database no Easypanel e linke nas variáveis de ambiente acima.

1.  **Postgres**: Crie um DB, copie a connection string e cole em `DATABASE_URL`.
2.  **Redis**: Crie um Redis, copie a connection string e cole em `REDIS_URL`.
