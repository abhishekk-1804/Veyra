# Architecture Overview

Veyra is split across a web application, an API service, and a set of packages
that hold the deterministic core of the product. This document describes the
boundaries and current implementation.

## Top-level components

```
apps/web      → Next.js front end (server-rendered + client React)
services/api  → FastAPI backend exposing HTTP endpoints
packages/     → shared/deterministic libraries (placeholders for now)
```

## Backend layering

`services/api` is organized into clear layers:

- **api/routes** — HTTP routers; parse/validate input, map to responses.
- **schemas** — Pydantic request/response models (the API contract). ORM
  objects are never exposed directly as the contract.
- **services** — application logic: orchestration, ownership enforcement.
- **repositories** — persistence access, scoped to a user.
- **domain** — enums and deterministic business rules, independent of web/UI,
  AI, and persistence.
- **models** — SQLAlchemy ORM models.
- **db** — engine/session configuration and the declarative base.

The domain and service layers are the only places business rules live. The web
app talks to the API over HTTP and never touches PostgreSQL directly.

## Boundaries and rules

1. **AI proposes, code decides.** The AI layer (packages/ai) will produce
   *proposals*. It never writes to the database directly. (Not yet implemented.)
2. **LLM output is untrusted input.** Any model output passes through schema
   validation before use. (Not yet implemented.)
3. **Deterministic business rules.** Rules live in the domain/service layers,
   not in prompts or UI components. Scheduling rules will be deterministic.
4. **Replaceable AI providers.** packages/ai defines a provider abstraction.
5. **Domain decoupled from UI.** packages/domain and the API domain module have
   no dependency on apps/web.
6. **API is the boundary.** The web app only reaches the backend through the
   API. It does not access the database directly.
7. **No premature microservices.** Only two deployable services exist: `web`
   and `api`.
8. **No speculative infrastructure.** Redis, pgvector, queues, workers, RAG,
   and agents are out of scope.

## Data access

The API owns database access. The web app never reaches the database directly.

## Database

PostgreSQL via SQLAlchemy, with schema changes managed by Alembic. The current
schema contains a single `goals` table. See `docs/architecture/development-setup.md`.

## Technology direction

| Concern     | Choice                                   |
|-------------|------------------------------------------|
| Front end   | Next.js, React, TypeScript, Tailwind CSS |
| Back end    | Python, FastAPI, Pydantic                 |
| Database    | PostgreSQL, SQLAlchemy, Alembic           |
| Development | Docker / Docker Compose, GitHub Actions  |