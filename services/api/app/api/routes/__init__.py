from app.api.routes.goals import router as base_goals_router
from app.api.routes.tasks import tasks_router, goals_router as goals_tasks_router
from app.api.routes.ai import ai_router
from app.api.routes.scheduling import scheduling_router

__all__ = ["base_goals_router", "goals_tasks_router", "tasks_router", "ai_router", "scheduling_router"]