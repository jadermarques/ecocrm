# BI Analytics API

Endpoints to consume aggregated metrics from the Mart layer. All endpoints are prefixed with `/api/v1/bi`.

## 1. Volume Metrics
**GET** `/volume`
- **Params**: `date_from`, `date_to`, `inbox_id` (optional).
- **Response**: Array of daily volume objects.

## 2. Agent Performance
**GET** `/agent-volume`
- **Params**: `date_from`, `date_to`.
- **Response**: Ranked list of agents by activity.

## 3. SLA & Time Metrics
**GET** `/time-metrics`
- **Params**: `date_from`, `date_to`, `inbox_id`.
- **Response**: Aggregate object with AVG, P50, P90 for response times.

## 4. Backlog Snapshot
**GET** `/backlog`
- **Params**: `inbox_id`.
- **Response**: Latest snapshot of backlog counts by status.
