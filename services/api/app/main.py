from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import base_goals_router, goals_tasks_router, tasks_router, ai_router, scheduling_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(base_goals_router)
app.include_router(goals_tasks_router)
app.include_router(tasks_router)
app.include_router(ai_router)
app.include_router(scheduling_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


# Mount static frontend if available
web_dir = Path(__file__).resolve().parent.parent.parent.parent / "apps" / "web"
if web_dir.exists() and (web_dir / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="static")