# API Documentation

## Base URL

The API runs locally at `http://localhost:8000`. Interactive docs are available
at `/docs` (Swagger UI) and `/redoc` (ReDoc) while the service is running.

## Authentication

Authentication is not implemented yet. Requests are associated with a single
development user. See [Development Setup](development-setup.md) for details.

## Goal model

| Field         | Type              | Notes                             |
|---------------|-------------------|-----------------------------------|
| `id`          | UUID              | Generated server-side             |
| `user_id`     | string            | Owner (development user for now)  |
| `title`       | string            | Required, non-blank, ≤ 120 chars  |
| `description` | string / null     | Optional                          |
| `status`      | enum              | `ACTIVE` / `COMPLETED` / `PAUSED` / `ARCHIVED` |
| `priority`    | enum              | `LOW` / `MEDIUM` / `HIGH` / `CRITICAL` |
| `target_date` | date / null       | Optional ISO date                 |
| `created_at`  | datetime          | Server set                        |
| `updated_at`  | datetime          | Server set                        |

## Endpoints

### GET /health

Returns service status.

```json
{ "status": "ok", "service": "Veyra API" }
```

### POST /goals

Create a goal. Body is a subset of the model above; only `title` is required.

**201** on success. **422** on invalid input (blank title, unknown enum, unknown field).

### GET /goals

List goals owned by the current development user, newest first.

**200** with a JSON array of goals.

### GET /goals/{id}

Get a single goal. Returns **404** if the goal does not exist or is not owned by
the current user.

### PATCH /goals/{id}

Partially update a goal. Any subset of editable fields may be sent. Returns
**200** with the updated goal, or **404** if not found / not owned. **422** on
invalid input.

## Error responses

Validation failures return **422** with FastAPI's standard detail body. Missing
resources return **404** with `{ "detail": "Goal not found" }`.