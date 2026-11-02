# Architecture Overview

Veyra is an independent AI-native execution and productivity platform organized as a monorepo with clear separation of concerns across presentation, API services, and deterministic domain cores.

## Top-Level Components

```
apps/web      → Vanilla HTML, modern CSS, and ES Modules frontend (served at /)
services/api  → FastAPI backend exposing validated HTTP endpoints
docs/         → Product, architecture, and API documentation
```

## Backend Layering (`services/api`)

The backend adheres strictly to layered Clean Architecture:

```
┌────────────────────────────────────────────────────────┐
│                   HTTP / API Layer                     │
│  app/main.py, app/api/routes/*.py, app/schemas/*.py    │
└──────────────────────────┬─────────────────────────────┘
                           │ (validates contracts & maps responses)
┌──────────────────────────▼─────────────────────────────┐
│                   Service Layer                        │
│               app/services/*.py                        │
└──────────────────────────┬─────────────────────────────┘
                           │ (enforces ownership & orchestrates domain)
┌──────────────────────────▼─────────────────────────────┐
│                 Repository Layer                       │
│              app/repositories/*.py                     │
└──────────────────────────┬─────────────────────────────┘
                           │ (executes user_id scoped queries)
┌──────────────────────────▼─────────────────────────────┐
│              Database / ORM Models                     │
│        app/models/*.py, app/db/session.py              │
└──────────────────────────┬─────────────────────────────┘
                           │ (persists entities via SQLAlchemy)
┌──────────────────────────▼─────────────────────────────┐
│             Domain Rules & Enums (Pure)                │
│                 app/domain/*.py                        │
└────────────────────────────────────────────────────────┘
```

- **`api/routes`**: Thin HTTP controllers handling dependency injection (`get_db`, `get_current_user_id`), transaction commits, and status mapping.
- **`schemas`**: Strict Pydantic v2 DTOs with `extra="forbid"` for writes and `from_attributes=True` for reads. ORM models are never directly exposed.
- **`services`**: Application orchestration (`GoalService`, `TaskService`, `AIPlannerService`). Enforces cross-aggregate ownership rules and executes atomic transactions.
- **`repositories`**: Data access abstraction scoped strictly to `user_id` to prevent cross-tenant access.
- **`domain`**: Pure Python standard library enums and validation rules with zero dependencies on frameworks, databases, or AI.
- **`models`**: SQLAlchemy 2.0 mapped declarative classes.
- **`ai`**: Provider abstraction, dev provider adapter, and proposal validation pipeline.
- **`scheduling`**: Pure deterministic scheduler implementing explainable task sequencing.

## Core Architectural Invariants

1. **AI Proposes, Code Decides**: AI providers produce untrusted plan proposals. AI code has no access to SQLAlchemy sessions, database repositories, or task mutation services.
2. **Untrusted AI Output**: Every proposal passes strict structural and business validation before persistence.
3. **Deterministic Business Rules**: All validation, state transitions, and sequencing algorithms are deterministic and explainable.
4. **Replaceable AI Provider Boundary**: Extensible `AIProvider` protocol. The core product functions completely with `DevAIProvider` without requiring external API keys.
5. **Atomic Task Creation**: Approving a proposal persists all planned tasks in a single database transaction via `TaskService.create_many()`.
6. **Proposal Idempotency**: Approving an already accepted proposal returns successfully without creating duplicate tasks.
7. **Anti-Tampering Integrity**: Stored proposals carry a SHA-256 fingerprint of the proposal payload, verified upon approval.
8. **Pure Scheduling Function**: Scheduling relies only on explicit inputs (`tasks`, `window`, `current_time`) and never queries system clocks, networks, or databases.
9. **Multi-Tenant Ownership Seam**: Authorization is enforced on every operation (`current_user_id == goal.user_id`, `current_user_id == task.user_id`, and `task.goal.user_id == current_user_id`). The development seam uses `X-Dev-User-Id` header overrides.

## Canonical Mutation Path for AI Plans

```
AIProvider
    ↓
AIPlannerService.generate_plan()
    ↓
validate_proposal()
    ↓
PlanProposal persistence (PENDING, with SHA-256 fingerprint)
    ↓
User explicitly clicks "Approve Plan"
    ↓
AIPlannerService.approve_proposal()
    ↓
Verify Ownership & Verify PENDING State
    ↓
Verify SHA-256 Fingerprint (Anti-tamper check)
    ↓
Re-validate Proposal Constraints
    ↓
TaskService.create_many() (Atomic bulk transaction)
    ↓
TaskRepository.add_all()
    ↓
Mark PlanProposal ACCEPTED
    ↓
SQLAlchemy commit & flush
    ↓
PostgreSQL
```

## Database Schema & Migrations

Managed via Alembic (`0001_create_goals`, `0002_add_tasks_and_proposals`):

- **`goals`**:
  - `id`: UUID (Primary Key)
  - `user_id`: String(64) (Indexed)
  - `title`: String(120)
  - `description`: Text (Nullable)
  - `status`: Enum (`ACTIVE`, `COMPLETED`, `PAUSED`, `ARCHIVED`)
  - `priority`: Enum (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
  - `target_date`: Date (Nullable)
  - `created_at`, `updated_at`: DateTime(timezone=True)
- **`tasks`**:
  - `id`: UUID (Primary Key)
  - `user_id`: String(64) (Indexed)
  - `goal_id`: UUID (Foreign Key to `goals.id` ON DELETE CASCADE, Indexed)
  - `title`: String(200)
  - `description`: Text (Nullable)
  - `status`: Enum (`TODO`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`)
  - `priority`: Enum (`LOW`, `MEDIUM`, `HIGH`, `URGENT`)
  - `estimated_minutes`: Integer (Nullable, 1–1440)
  - `due_date`: DateTime(timezone=True) (Nullable)
  - `created_at`, `updated_at`: DateTime(timezone=True)
- **`plan_proposals`**:
  - `id`: UUID (Primary Key)
  - `user_id`: String(64) (Indexed)
  - `goal_id`: UUID (Foreign Key to `goals.id` ON DELETE CASCADE)
  - `status`: Enum (`PENDING`, `ACCEPTED`, `REJECTED`)
  - `proposal_payload`: Text (Serialized JSON)
  - `fingerprint`: String(64) (SHA-256 hash)
  - `created_at`: DateTime(timezone=True)
  - `expires_at`: DateTime(timezone=True) (Nullable)

## Deterministic Scheduling Algorithm

The scheduling function `generate_schedule(tasks, window, current_time)` is a pure function. Tasks are sorted using a deterministic 8-tier tuple:

1. `is_completed`: Active/incomplete before completed/cancelled (`False < True`)
2. `is_todo`: `IN_PROGRESS` before `TODO` (`False < True`)
3. `has_no_due_date`: Dated tasks before undated tasks (`False < True`)
4. `due_date_timestamp`: Earlier UTC timestamp first
5. `priority_rank`: `URGENT` (0) > `HIGH` (1) > `MEDIUM` (2) > `LOW` (3)
6. `estimated_minutes`: Shorter duration first
7. `created_at_timestamp`: Earlier creation timestamp first
8. `task_id`: Lexicographical UUID tie-breaker

Tasks are sequentially packed into `window.available_minutes`. If a task exceeds the remaining window capacity, it is appended to `deferred`.