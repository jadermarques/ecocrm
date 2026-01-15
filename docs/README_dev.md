# Guia de Desenvolvimento e Persistência

## Comandos Docker

Comandos essenciais para rodar o ambiente local. Use o **Makefile** para facilitar.

```bash
# Subir a stack (Buildando as imagens se necessário)
make up # ou: docker compose up -d --build

# Verificar status dos containers
make ps # ou: docker compose ps

# Acompanhar logs
make logs # ou: docker compose logs -f

# Resetar (CUIDADO: Apaga volumes)
make reset # ou: docker compose down -v --remove-orphans
```

## Persistência de Dados

Descrevemos abaixo como os dados são mantidos entre reinicializações e ambientes.

### 1. Banco de Dados (Postgres)
- **Status**: Sempre persistente.
- **Mecanismo**: Volume nomeado Docker (`postgres_data`).
- **Caminho Interno**: `/var/lib/postgresql/data`

### 2. Cache e Filas (Redis)
- **Status**: Opcionalmente persistente.
- **Mecanismo**: Volume nomeado Docker (`redis_data`) + AOF (Append Only File) ativado.
- **Caminho Interno**: `/data`

### 3. Arquivos da Aplicação (App Data)
Diferenciamos o comportamento entre Desenvolvimento (DEV) e Produção (PROD).

| Tipo | Local | Host (DEV) | Container | Descrição |
|---|---|---|---|---|
| **Uploads** | Arquivos de KB/RAG | `./var/uploads` | `/app/data/uploads` | Arquivos enviados por usuários. |
| **Exports** | Relatórios | `./var/exports` | `/app/data/exports` | CSVs ou relatórios gerados. |
| **Tmp** | Temporários | `./var/tmp` | `/app/data/tmp` | Processamento volátil. |

**Notas Importantes:**
- Em **DEV**, usamos *bind mounts* para mapear `./var` do host para `/app/data`. Isso facilita debug e acesso direto aos arquivos.
- Em **PROD**, deve-se usar volumes nomeados (ex: `app_data`) para isolamento e segurança.

## Acessos Locais

| Serviço | URL | Descrição |
|---|---|---|
| **Health Check API** | `http://localhost:8000/health` | Status da API |
| **Documentação API** | `http://localhost:8000/docs` | Swagger UI |
| **Portal Streamlit** | `http://localhost:8501` | Interface Administrativa |

## Testando Webhooks (Chatwoot)

O sistema agora salva os eventos brutos no Postgres antes de processar.

**Exemplo CURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/chatwoot?t=SEU_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "event": "message_created",
           "message_type": "incoming",
           "account": {"id": 1},
           "data": {
             "id": 12345,
             "content": "Teste P2 Persistence",
             "inbox": {"id": 1},
             "conversation": {"id": 10},
             "sender": {"id": 99, "name": "Tester", "phone_number": "+5511999999999"}
           }
         }'
```

Se bem sucedido:
1. Retorna `{"status": "processed", "message_id": ..., "raw_id": ...}`
2. Insere registro na tabela `chatwoot_webhook_events_raw`.
3. Publica no Redis `events:chatwoot`.

## Test Lab (Bot Studio)
O Backend do Test Lab agora suporta persistência.
- **POST** `/api/v1/testlab/runs`: Cria uma sessão.
- **POST** `/api/v1/testlab/runs/{run_id}/messages`: Envia mensagem.
- **GET** `/api/v1/testlab/runs/{run_id}/events`: Lista histórico da sessão.
