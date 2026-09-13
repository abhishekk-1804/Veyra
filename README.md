# Veyra

Veyra is an independent, AI-native execution and productivity platform. It helps
people get things done by combining deterministic application logic with an AI
layer that proposes actions rather than mutating state directly.

## Status

Early development. Phase 1 establishes the **Goal** domain and a minimal
end-to-end create/list/read/update workflow backed by FastAPI and PostgreSQL.
Authentication, AI, projects, tasks, scheduling, and other features are not yet
implemented.

## Repository layout

```
Veyra/
  apps/
    web/          # Next.js web application (TypeScript, Tailwind CSS)
  services/
    api/          # FastAPI service (Python, Pydantic)
  packages/
    domain/        # Deterministic domain & business rules
    ai/            # AI provider abstraction & validation
    scheduling/    # Deterministic scheduling logic
    shared/        # Shared utilities & types
  docs/
    product/       # Product documentation
    architecture/  # Architecture documentation
    api/           # API documentation
```

## Guiding architectural principles

- The AI layer proposes changes; it does not directly mutate the database.
- LLM output is untrusted input and is always validated.
- Deterministic application/domain code owns business rules.
- Scheduling logic is deterministic, never delegated wholesale to an LLM.
- AI providers are replaceable; nothing is hard-coded around a single vendor.
- Domain logic does not depend on the web UI.
- No microservices beyond the `web` / `api` separation at this stage.

## Getting started

See [docs/architecture/development-setup.md](docs/architecture/development-setup.md) for how to run the web app and API locally.