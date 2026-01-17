# Database Migration Required

> [!WARNING]
> **Action Required:** Database Migration

The Bot Studio expansion adds **31 new columns** across three tables. You must either:

## Option 1: Using Alembic (Recommended)

```bash
# Inside the platform_api container
docker exec -it ecocrm-platform_api-1 bash

# Generate migration
alembic revision --autogenerate -m "Add CrewAI attributes"

# Review the generated migration file
# Apply the migration
alembic upgrade head
```

## Option 2: Manual SQL

Execute the SQL script below in your PostgreSQL database:

```sql
-- BotAgent - 11 new columns
ALTER TABLE bot_agents ADD COLUMN backstory TEXT;
ALTER TABLE bot_agents ADD COLUMN llm VARCHAR;
ALTER TABLE bot_agents ADD COLUMN function_calling_llm VARCHAR;
ALTER TABLE bot_agents ADD COLUMN max_iter INTEGER DEFAULT 20;
ALTER TABLE bot_agents ADD COLUMN max_rpm INTEGER;
ALTER TABLE bot_agents ADD COLUMN max_execution_time INTEGER;
ALTER TABLE bot_agents ADD COLUMN verbose BOOLEAN DEFAULT FALSE;
ALTER TABLE bot_agents ADD COLUMN allow_delegation BOOLEAN DEFAULT FALSE;
ALTER TABLE bot_agents ADD COLUMN reasoning BOOLEAN DEFAULT FALSE;
ALTER TABLE bot_agents ADD COLUMN knowledge_sources JSON;

-- BotTask - 8 new columns
ALTER TABLE bot_tasks ADD COLUMN tools_json JSON;
ALTER TABLE bot_tasks ADD COLUMN context_task_ids JSON;
ALTER TABLE bot_tasks ADD COLUMN async_execution BOOLEAN DEFAULT FALSE;
ALTER TABLE bot_tasks ADD COLUMN output_json_schema JSON;
ALTER TABLE bot_tasks ADD COLUMN output_pydantic_schema JSON;
ALTER TABLE bot_tasks ADD COLUMN callback_config JSON;
ALTER TABLE bot_tasks ADD COLUMN guardrail_config JSON;
ALTER TABLE bot_tasks ADD COLUMN guardrail_max_retries INTEGER DEFAULT 3;

-- BotCrew - 12 new columns
ALTER TABLE bot_crews ADD COLUMN verbose BOOLEAN DEFAULT FALSE;
ALTER TABLE bot_crews ADD COLUMN max_rpm INTEGER;
ALTER TABLE bot_crews ADD COLUMN manager_llm VARCHAR;
ALTER TABLE bot_crews ADD COLUMN function_calling_llm VARCHAR;
ALTER TABLE bot_crews ADD COLUMN manager_agent_id INTEGER REFERENCES bot_agents(id);
ALTER TABLE bot_crews ADD COLUMN config_json JSON;
ALTER TABLE bot_crews ADD COLUMN memory_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE bot_crews ADD COLUMN knowledge_sources JSON;
ALTER TABLE bot_crews ADD COLUMN step_callback_config JSON;
ALTER TABLE bot_crews ADD COLUMN task_callback_config JSON;
ALTER TABLE bot_crews ADD COLUMN output_log_file VARCHAR;
ALTER TABLE bot_crews ADD COLUMN share_crew BOOLEAN DEFAULT FALSE;
```

## Verification

After migration, verify the changes:

```sql
-- Check bot_agents structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'bot_agents';

-- Check bot_tasks structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'bot_tasks';

-- Check bot_crews structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'bot_crews';
```
