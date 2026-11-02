# Development Setup

How to run Veyra locally.

## Prerequisites

- Python 3.12+ (or 3.11+)
- (Optional) Docker, for the local PostgreSQL database

No Node.js, npm, or frontend build toolchains are required. The frontend is built with vanilla HTML, modern CSS, and ES Modules.

## Database

The default `DATABASE_URL` points at a local PostgreSQL instance matching the Docker Compose service:

```bash
docker compose up -d db
```

If Docker is unavailable, the test suite runs completely independently against an in-memory SQLite database via pytest.

### Applying Migrations

Run Alembic migrations from the API directory:

```bash
cd services/api
.venv\Scripts\alembic.exe upgrade head    # Windows
# source .venv/bin/alembic upgrade head   # macOS / Linux
```

The database schema manages:
- `goals`: Core user objectives and milestones
- `tasks`: Goal-scoped actionable work items with priorities and time estimates
- `plan_proposals`: Intermediate AI proposal artifacts awaiting user approval

## Running Veyra (Backend & Frontend)

Because the frontend is served directly as static files by FastAPI at `/`, starting the backend runs the entire platform:

```bash
cd services/api
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS / Linux
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

- Web Platform: <http://localhost:8000>
- Health Check: <http://localhost:8000/health>
- Interactive API Docs: <http://localhost:8000/docs>

### Configuration

Copy `.env.example` to `.env` and adjust values. `.env` is ignored by git.
The API reads:

- `DATABASE_URL` — SQLAlchemy connection string (defaults to `postgresql+psycopg://veyra:veyra@localhost:5432/veyra`).
- `DEV_USER_ID` — the development user identity (default `dev-user`).
- `CORS_ORIGINS` — comma-separated origins allowed to call the API (default `http://localhost:8000,http://localhost:3000`).

### Development Identity Seam

Authentication is decoupled from authorization via a development seam. Every request is scoped to a user (`dev_user_id`), which can be overridden per request via the `X-Dev-User-Id` header for automated multi-tenant testing without mock auth services.

### AI Provider Setup

Veyra V1 operates completely without external API keys. It defaults to `DevAIProvider`, a deterministic development provider that generates structured plan proposals for testing and development. Real external providers can be injected via the `AIProvider` protocol.

### Running Backend Tests

```bash
cd services/api
.venv\Scripts\pytest.exe -v
```

Automated tests run against an isolated in-memory SQLite database using SQLAlchemy's `StaticPool`. No running PostgreSQL or external network connection is required.