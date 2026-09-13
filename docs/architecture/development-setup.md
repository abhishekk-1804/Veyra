# Development Setup

How to run the web app and the API locally.

## Prerequisites

- Node.js 20+ (plus npm)
- Python 3.11+
- (Optional) Docker, for the PostgreSQL database

## Database

The default `DATABASE_URL` points at a local PostgreSQL instance matching the
Docker Compose service:

```bash
docker compose up -d db
```

If Docker is unavailable, you can point `DATABASE_URL` at any PostgreSQL you
have access to (see Configuration below).

### Applying migrations

Run Alembic migrations from the API directory:

```bash
cd services/api
.venv\Scripts\alembic.exe upgrade head    # Windows
# source .venv/bin/alembic upgrade head   # macOS / Linux
```

The schema currently contains a single `goals` table.

## API service

```bash
cd services/api
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS / Linux
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Runs the FastAPI app at <http://localhost:8000>. Health check:
<http://localhost:8000/health>.

### Configuration

Copy `.env.example` to `.env` and adjust values. `.env` is ignored by git.
The API reads:

- `DATABASE_URL` — SQLAlchemy connection string (defaults to the local
  `postgresql+psycopg://veyra:veyra@localhost:5432/veyra`).
- `DEV_USER_ID` — the development user owning goals until real auth exists.
- `CORS_ORIGINS` — comma-separated origins allowed to call the API.

### Development user (no auth yet)

Authentication is not implemented. The API associates every request with a
single development user, configured via `DEV_USER_ID` (default `dev-user`).
For local testing you can override the identity per request with the
`X-Dev-User-Id` header. This is a development-only seam; real authentication
will replace it.

### Tests

```bash
pytest
```

Tests run against an in-memory SQLite database, so they do not require a
running PostgreSQL instance.

## Web app

```bash
cd apps/web
npm install
npm run dev
```

Runs the Next.js dev server at <http://localhost:3000>. The Goals page is at
<http://localhost:3000/goals>.

### Configuration

Copy `apps/web/.env.example` to `.env` to set `NEXT_PUBLIC_API_URL`
(default `http://localhost:8000`).

### Checks

```bash
npm run lint     # ESLint
npm run build    # production build (includes type checking)
npx tsc --noEmit # typecheck
```