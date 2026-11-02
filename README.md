# Veyra

Veyra is an independent, AI-native execution and productivity platform. It helps users plan, sequence, and execute work by combining deterministic application logic with an AI proposal layer.

Veyra is built from the ground up with its own domain architecture, API contracts, deterministic scheduling engine, and execution workflow.

## Core Principle

> **AI Proposes. Deterministic Application Code Decides and Executes.**

LLMs are treated as untrusted external inputs. An AI model never directly mutates application state or schedules tasks. Every plan proposal undergoes structural and business validation, requires explicit human review and approval, and is persisted atomically by application domain services.

```
USER INTENT (Goal)
       ↓
AI-ASSISTED PLANNING
       ↓
STRUCTURED PROPOSAL (PlanProposal)
       ↓
VALIDATION (Structural & Invariant Checks)
       ↓
USER REVIEW (Human Approval Gate)
       ↓
EXPLICIT APPROVAL
       ↓
ATOMIC TASK CREATION (TaskService)
       ↓
DETERMINISTIC SCHEDULING (Sequential Capacity Allocation)
       ↓
EXECUTION & PROGRESS TRACKING
       ↓
REVIEWABLE REPLANNING
```

## V1 Capabilities

1. **Goal Management**: Define high-level intents with description, target dates, and status tracking.
2. **Task Domain**: Goal-scoped tasks with strictly bounded estimates, state machine transitions (`TODO`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`), and priorities (`LOW`, `MEDIUM`, `HIGH`, `URGENT`).
3. **Replaceable AI Provider Boundary**: Extensible `AIProvider` protocol with a deterministic `DevAIProvider` for local testing without external API keys.
4. **Untrusted AI Proposal Pipeline**: Intermediate reviewable `plan_proposals` with SHA-256 fingerprinting for anti-tampering and idempotent approval.
5. **Deterministic Scheduling Engine**: Pure function ordering tasks via 8 explicit rules into execution windows without system-clock or network dependencies.
6. **Execution & Progress Tracking**: Real-time progress bars, current focus spotlight, scheduled sequence offsets, and deferred queue ranking.
7. **Reviewable Replanning**: Proposes explicit adjustments (`ESCALATE_PRIORITY`, `RESCHEDULE_NEXT_WINDOW`) for overdue deadlines and deferred tasks without silent state mutation.
8. **Native Vanilla Frontend**: Zero framework bloat, responsive dark-themed workspace built with pure HTML, modern CSS, and ES Modules served directly by FastAPI.

## Repository Layout

```
Veyra/
  apps/
    web/          # Vanilla HTML, CSS, and ES Modules frontend (served at /)
  services/
    api/          # FastAPI backend (Python 3.12, SQLAlchemy 2.0, Pydantic v2, Alembic)
  docs/
    product/      # Product concept & user workflows
    architecture/ # Architecture overview & development setup
    api/          # REST API contracts & endpoint specifications
```

## Technology Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic
- **Database**: PostgreSQL (production/local dev) / SQLite in-memory (automated test suites)
- **Frontend**: Pure HTML5, modern CSS3 (Zinc palette), vanilla JavaScript (ES Modules)
- **Testing**: pytest (77 unit, integration, and API tests)
- **CI**: GitHub Actions (automated test runner and frontend validation)

## Getting Started

See [docs/architecture/development-setup.md](docs/architecture/development-setup.md) for local environment setup, running tests, and starting the platform.