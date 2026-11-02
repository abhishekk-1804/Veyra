# Product Overview

Veyra is an independent AI-native execution and productivity platform. It is designed to bridge the gap between high-level human intent and grounded, sequential execution.

## Vision

Veyra provides a reliable, deterministic system for getting things done. Instead of treating language models as autonomous agents that silently mutate state, Veyra enforces a strict separation:

1. **AI Proposes**: Large language models excel at synthesizing intent, generating task breakdowns, estimating effort, and suggesting priority structures.
2. **Deterministic Rules Validate and Execute**: Application domain services enforce strict validation invariants, multi-tenant ownership boundaries, atomic state persistence, and reproducible mathematical scheduling.
3. **Human Decides**: The user reviews intermediate structured proposals and retains explicit approval authority before any tasks are created or modified.

## Core Product Workflow

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

## Domain Hierarchy

Veyra V1 operates on a clean, direct domain structure:

```
Goal → Tasks
```

- **Goal**: Represents a broad outcome or intent (e.g., "Launch Veyra V1", "Prepare Q3 Architecture Review"). Has title, description, status (`ACTIVE`, `COMPLETED`, `PAUSED`, `ARCHIVED`), priority (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), and target date.
- **Task**: An atomic, actionable unit of work linked directly to a parent Goal (`tasks.goal_id -> goals.id` with `ON DELETE CASCADE`). Has title (1–200 characters), description (up to 2000 characters), status (`TODO`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`), priority (`LOW`, `MEDIUM`, `HIGH`, `URGENT`), bounded estimate (1–1440 minutes), and optional due date.
- **Plan Proposal**: An untrusted, reviewable intermediate artifact (`plan_proposals`) with SHA-256 fingerprinting, tracking proposed tasks, estimates, and priorities until approved or rejected.

## AI Planning & Approval Boundaries

- The AI provider produces an untrusted `PlanProposal`.
- The system executes structural and business validation:
  - Max 15 tasks per proposal.
  - Max 4800 total estimated minutes.
  - Per-task title (1–200 chars) and notes (up to 2000 chars) bounds.
  - Estimate bounds (1–1440 minutes).
  - Valid priority and ISO date formats.
- Approval is strictly idempotent: approving an already accepted proposal never duplicates tasks.
- Rejection creates exactly zero tasks and prevents subsequent approval.

## Deterministic Scheduling

Veyra does not ask an LLM to order your calendar. Scheduling is a pure, explainable function that places tasks sequentially into an execution window (e.g. 120 minutes) using 8 deterministic rules:

1. Active/incomplete tasks before completed/cancelled tasks
2. `IN_PROGRESS` tasks before `TODO` tasks
3. Earlier due date first
4. Tasks with due dates before tasks without due dates
5. Higher priority first (`URGENT` > `HIGH` > `MEDIUM` > `LOW`)
6. Shorter estimated duration first
7. Earlier creation timestamp first
8. Stable task UUID as final tie-breaker

Tasks exceeding the window capacity are categorized as deferred, with explicit explanation for why they were deferred.

## Reviewable Replanning

When tasks are overdue, cancelled, or deferred beyond capacity, Veyra's replanning assistant analyzes the execution bottleneck and presents proposed adjustments (such as escalating priority or deferring slots). No task is silently updated—every adjustment requires human approval.