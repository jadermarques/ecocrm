# Data Hub Architecture

The Data Hub is responsible for ensuring all Chatwoot data is captured, persisted in a raw format, and then transformed for analytics.

## 1. Data Ingestion Flow

### A. Real-time (Webhook)
1. **Source**: Chatwoot sends Webhook events to `POST /api/v1/webhooks/chatwoot`.
2. **Persistence**:
   - The payload is saved **as-is** into the `raw_chatwoot_events` table (Postgres).
   - `is_valid` flag indicates if initial processing succeeded.
3. **Distribution**:
   - Valid `message_created` events are published to Redis Stream (`events:chatwoot`).
   - `bot_runner` consumes these events for real-time automation.

### B. Backfill (Worker)
1. **Source**: `data_hub_runner` service polls Chatwoot API.
2. **Frequency**: Configurable via `DATA_HUB_BACKFILL_INTERVAL_SECONDS` (default 30m).
3. **Logic**:
   - Iterates all Conversations (Status: All).
   - Upserts to `raw_chatwoot_conversations`.
   - Fetches & Upserts Messages to `raw_chatwoot_messages`.
   - Fetches & Upserts Reporting Events to `raw_chatwoot_reporting_events`.
   - **Reliability**: Uses `ON CONFLICT UPDATE` to ensure idempotency.

## 2. Data Hub Runner
The worker is a separate Python process found in `data_hub_runner/worker.py`.

### Running Locally
```bash
# Using Docker Compose
docker compose up -d data_hub_runner

# Manually
export PYTHONPATH=$PYTHONPATH:.
python data_hub_runner/worker.py
```

### Environment Variables
- `CHATWOOT_BASE_URL`
- `CHATWOOT_API_TOKEN` (User Access Token)
- `CHATWOOT_ACCOUNT_ID`
- `DATA_HUB_BACKFILL_INTERVAL_SECONDS`
