# BI Data Model (Postgres)

We use a layered approach (ELT) to transform raw data into actionable metrics.

## 1. Raw Layer (Tables)
Mirrors source API/Webhooks.
- `raw_chatwoot_events`: All webhook payloads.
- `raw_chatwoot_conversations`: Conversation objects.
- `raw_chatwoot_messages`: Message objects.
- `raw_chatwoot_reporting_events`: SLA/metrics events.

## 2. Staging Layer (Views)
Normalizes data types and JSON extraction.
- `stg_conversations`: Extracts `unread_count`, dates.
- `stg_messages`: Computes `content_length`, `has_attachment`.
- `stg_reporting_events`: Filters relevant fields.

## 3. Mart Layer (Materialized Views)
Aggregates data for high-performance querying by the API.

| Mart View | Description | Key Metrics |
|-----------|-------------|-------------|
| `mart_inbox_daily_volume` | Daily metrics per inbox | conversations_count, messages_count |
| `mart_agent_daily_volume` | Agent performance daily | messages_count, conversations_touched |
| `mart_conversation_time_metrics` | SLA metrics per conversation | first_response, resolution, reply_time (avg/p50/90) |
| `mart_backlog_snapshot` | Historical backlog state | open, pending, snoozed counts |

## Refresh Strategy
- **Routine**: `data_hub_runner` triggers a refresh after every backfill cycle.
- **Method**: `REFRESH MATERIALIZED VIEW CONCURRENTLY`.
- **Backlog**: Inserts a new row into `mart_backlog_snapshot` table with `NOW()` timestamp.
