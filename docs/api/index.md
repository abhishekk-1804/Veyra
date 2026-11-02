# API Documentation

## Base URL

The API runs locally at `http://localhost:8000`. Interactive OpenAPI documentation is available at `/docs` (Swagger UI) and `/redoc` (ReDoc) while the service is running.

## Authentication & Authorization Seam

Authentication is not yet implemented. All requests are associated with a user identity resolved via the development seam:
- Default: `dev_user_id` from configuration (default `"dev-user"`).
- Per-request override: `X-Dev-User-Id` request header for testing tenant isolation.

Every endpoint verifies that:
1. The authenticated user owns the resource being accessed.
2. For nested resources (e.g. tasks under a goal), the authenticated user owns both the task and the parent goal.
3. Access to non-existent or cross-tenant resources returns **404 Not Found** (preventing enumeration attacks).

---

## Data Models

### Goal Model

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key (generated server-side) |
| `user_id` | string | Owner ID |
| `title` | string | Required, non-blank, ≤ 120 characters |
| `description` | string / null | Optional notes |
| `status` | enum | `ACTIVE`, `COMPLETED`, `PAUSED`, `ARCHIVED` (default: `ACTIVE`) |
| `priority` | enum | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` (default: `MEDIUM`) |
| `target_date` | date / null | Optional target deadline (ISO format) |
| `created_at` | datetime | Creation timestamp (UTC) |
| `updated_at` | datetime | Last update timestamp (UTC) |

### Task Model

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key (generated server-side) |
| `user_id` | string | Owner ID |
| `goal_id` | UUID | Foreign key to `goals.id` (`ON DELETE CASCADE`) |
| `title` | string | Required, non-blank, 1–200 characters |
| `description` | string / null | Optional notes (≤ 2000 characters) |
| `status` | enum | `TODO`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED` (default: `TODO`) |
| `priority` | enum | `LOW`, `MEDIUM`, `HIGH`, `URGENT` (default: `MEDIUM`) |
| `estimated_minutes` | int / null | Optional effort estimate (1–1440 minutes) |
| `due_date` | datetime / null | Optional due timestamp (ISO format) |
| `created_at` | datetime | Creation timestamp (UTC) |
| `updated_at` | datetime | Last update timestamp (UTC) |

### Plan Proposal Model

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key (generated server-side) |
| `user_id` | string | Owner ID |
| `goal_id` | UUID | Foreign key to `goals.id` (`ON DELETE CASCADE`) |
| `status` | enum | `PENDING`, `ACCEPTED`, `REJECTED` |
| `proposal_payload` | string | JSON string containing structured proposal and tasks |
| `fingerprint` | string | SHA-256 hash of `proposal_payload` for tamper verification |
| `created_at` | datetime | Creation timestamp (UTC) |
| `expires_at` | datetime / null | Optional proposal expiration |

---

## Endpoints

### System

#### `GET /health`
Returns service status and name.

```json
{
  "status": "ok",
  "service": "Veyra API"
}
```

---

### Goals (`/goals`)

- `POST /goals` — Create a goal. **201 Created** or **422 Unprocessable Entity**.
- `GET /goals` — List goals owned by current user. **200 OK**.
- `GET /goals/{goal_id}` — Get single goal. **200 OK** or **404 Not Found**.
- `PATCH /goals/{goal_id}` — Update goal fields. **200 OK**, **404**, or **422**.

---

### Tasks (`/goals/{goal_id}/tasks` and `/tasks/{task_id}`)

- `POST /goals/{goal_id}/tasks` — Create a task under a goal. The goal must be owned by the user. **201 Created**, **404**, or **422**.
- `GET /goals/{goal_id}/tasks` — List all tasks belonging to the specified goal. **200 OK** or **404**.
- `GET /tasks/{task_id}` — Get a task by ID. **200 OK** or **404**.
- `PATCH /tasks/{task_id}` — Update task details or transition status. Enforces valid state transitions (`TODO` ↔ `IN_PROGRESS`, `TODO`/`IN_PROGRESS` → `COMPLETED`/`CANCELLED`). **200 OK**, **404**, or **422**.
- `DELETE /tasks/{task_id}` — Delete a task. **204 No Content** or **404**.

---

### AI Planning (`/ai/plans`)

- `POST /ai/plans` — Generate an AI plan proposal for a goal.
  - Request: `{"goal_id": "<uuid>", "prompt": "..."}`
  - Validates provider output (max 15 tasks, max 4800 min, bounds, non-blank titles).
  - Persists proposal as `PENDING` with SHA-256 fingerprint.
  - Returns `ProposalRead` (**201 Created**).
- `POST /ai/plans/{proposal_id}/approve` — Explicitly approve proposal.
  - Verifies ownership and `PENDING` state.
  - Verifies SHA-256 fingerprint against payload to prevent tampering.
  - Re-validates proposal constraints.
  - Atomically creates all planned tasks via `TaskService.create_many()`.
  - Marks proposal `ACCEPTED`. Idempotent: subsequent approvals return without duplicate task creation.
  - Returns created `list[TaskRead]` (**200 OK**).
- `POST /ai/plans/{proposal_id}/reject` — Explicitly reject proposal.
  - Marks proposal `REJECTED`. Creates zero tasks. **204 No Content**.

---

### Deterministic Scheduling (`/goals/{goal_id}/schedule`)

- `POST /goals/{goal_id}/schedule` — Generate an execution plan for a goal's tasks.
  - Request:
    ```json
    {
      "start_time": "2026-09-27T12:00:00Z",
      "available_minutes": 120
    }
    ```
  - Pure deterministic ordering via 8 strict rules:
    1. Active before completed/cancelled
    2. `IN_PROGRESS` before `TODO`
    3. Earlier due date first
    4. Dated tasks before undated tasks
    5. Higher priority first (`URGENT` > `HIGH` > `MEDIUM` > `LOW`)
    6. Shorter estimated duration first
    7. Earlier creation timestamp first
    8. Task UUID as stable tie-breaker
  - Returns `ExecutionPlan` (**200 OK**):
    ```json
    {
      "scheduled": [
        {
          "task_id": "...",
          "title": "Implement core algorithm",
          "status": "TODO",
          "priority": "HIGH",
          "estimated_minutes": 60,
          "due_date": null,
          "start_offset": 0,
          "end_offset": 60
        }
      ],
      "deferred": [],
      "total_scheduled_minutes": 60,
      "total_deferred_minutes": 0
    }
    ```