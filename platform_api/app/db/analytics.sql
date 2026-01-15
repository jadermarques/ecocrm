-- STG LAYERS (Views)

CREATE OR REPLACE VIEW stg_conversations AS
SELECT
    conversation_id,
    inbox_id,
    status,
    assignee_id,
    contact_id,
    created_at_ts AS created_at,
    updated_at_ts AS updated_at,
    (payload_json->>'last_activity_at')::timestamp as last_activity_at,
    (payload_json->>'unread_count')::int as unread_count
FROM raw_chatwoot_conversations;

CREATE OR REPLACE VIEW stg_messages AS
SELECT
    message_id,
    conversation_id,
    inbox_id,
    sender_type,
    message_type,
    private AS is_private,
    created_at_ts AS created_at,
    LENGTH(content) AS content_length,
    CASE WHEN jsonb_array_length(payload_json->'attachments') > 0 THEN true ELSE false END AS has_attachment
FROM raw_chatwoot_messages;

CREATE OR REPLACE VIEW stg_reporting_events AS
SELECT
    reporting_event_id,
    conversation_id,
    inbox_id,
    user_id,
    name,
    value_seconds,
    value_business_hours_seconds,
    event_start_time,
    event_end_time
FROM raw_chatwoot_reporting_events
WHERE conversation_id IS NOT NULL; -- Ensure linked to conversation

-- MART LAYERS (Materialized Views for Performance / Snapshot Table for Backlog)

-- 1. Inbox Daily Volume
CREATE MATERIALIZED VIEW IF NOT EXISTS mart_inbox_daily_volume AS
SELECT
    DATE(created_at) as day,
    inbox_id,
    COUNT(DISTINCT conversation_id) as conversations_count,
    COUNT(message_id) as messages_count
FROM stg_messages
GROUP BY 1, 2
ORDER BY 1 DESC;

-- 2. Agent Daily Volume
CREATE MATERIALIZED VIEW IF NOT EXISTS mart_agent_daily_volume AS
SELECT
    DATE(created_at) as day,
    sender_id as user_id,
    COUNT(message_id) as messages_count,
    COUNT(DISTINCT conversation_id) as conversations_touched
FROM stg_messages
WHERE sender_type = 'User'
GROUP BY 1, 2
ORDER BY 1 DESC;

-- 3. Conversation Time Metrics
-- Derived from reporting events primarily, or calculated if not available.
-- Chatwoot exports 'first_response', 'resolution', 'reply_time' events.
CREATE MATERIALIZED VIEW IF NOT EXISTS mart_conversation_time_metrics AS
SELECT
    conversation_id,
    inbox_id,
    MAX(CASE WHEN name = 'first_response' THEN value_seconds END) as first_response_seconds,
    MAX(CASE WHEN name = 'conversion_resolution' OR name = 'resolution' THEN value_seconds END) as resolution_seconds,
    AVG(CASE WHEN name = 'reply_time' THEN value_seconds END) as reply_time_seconds,
    MAX(CASE WHEN name = 'first_response' THEN value_business_hours_seconds END) as first_response_bh_seconds,
    MAX(CASE WHEN name = 'conversion_resolution' OR name = 'resolution' THEN value_business_hours_seconds END) as resolution_bh_seconds
FROM stg_reporting_events
GROUP BY 1, 2;

-- 4. Backlog Snapshot Table (History)
CREATE TABLE IF NOT EXISTS mart_backlog_snapshot (
    snapshot_ts TIMESTAMP DEFAULT NOW(),
    inbox_id INT,
    status VARCHAR,
    count INT
);

-- Indices
CREATE UNIQUE INDEX IF NOT EXISTS idx_mart_inbox_daily ON mart_inbox_daily_volume (day, inbox_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mart_agent_daily ON mart_agent_daily_volume (day, user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mart_conv_metrics ON mart_conversation_time_metrics (conversation_id);
