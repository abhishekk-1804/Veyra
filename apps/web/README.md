# Veyra Web Frontend

Vanilla HTML, CSS, and modern JavaScript (ES Modules) single-page execution platform interface.

## Architecture

- **No Framework Overheads**: Pure vanilla web standard implementation. Strictly zero React, zero TypeScript compile step, zero node_modules required.
- **Direct Backend Integration**: Mounted and served directly by the FastAPI backend at `/` or independently via any static HTTP web server.
- **Modular Design**:
  - `css/`: Modular stylesheets (`base.css`, `layout.css`, `components.css`, `dashboard.css`, `goals.css`, `planner.css`, `execution.css`).
  - `js/`: ES Modules (`app.js`, `api.js`, `state.js`, `router.js`, `ui.js`, `dashboard.js`, `goals.js`, `planner.js`, `execution.js`).
  - `index.html`: Shell mounting the responsive dark-themed workspace.

## Core Workspaces

1. **Dashboard (`#dashboard`)**: System stats, completion metrics, and transparent 4-stage lifecycle flow (`Intent -> Propose -> Decide -> Execute`).
2. **Goals & Tasks (`#goals`)**: Master-detail workspace with progress tracking, task CRUD, status machine transitions, and priority tagging.
3. **AI Planner (`#planner`)**: Bounded intent decomposition proposals with transparent review, approval, and rejection.
4. **Execution Engine (`#execution`)**: Deterministic dispatch bounded by capacity windows, immediate focus spotlight, and reviewable replanning with explicit user control.

## Running Locally

Served automatically when launching the FastAPI backend:

```bash
cd services/api
uvicorn app.main:app --reload --port 8000
```

Navigate to `http://localhost:8000`.
