from app.ai.provider import AIProvider, PlannedTask, PlanProposal

class DevAIProvider(AIProvider):
    """Deterministic dev provider that returns predictable proposals."""

    def generate_plan(self, goal_title: str, goal_description: str | None, prompt: str) -> PlanProposal:
        tasks = [
            PlannedTask(
                title=f"Initial research for {goal_title}",
                notes="Gather requirements and understand the scope.",
                estimated_minutes=60,
                priority="HIGH"
            ),
            PlannedTask(
                title=f"Draft design for {goal_title}",
                notes="Create a preliminary design based on research.",
                estimated_minutes=120,
                priority="MEDIUM"
            ),
            PlannedTask(
                title=f"Implementation of {goal_title}",
                notes="Write the code.",
                estimated_minutes=240,
                priority="URGENT"
            ),
        ]
        return PlanProposal(
            goal_id="dummy", # This will be overridden
            summary="A deterministic dev plan",
            tasks=tasks
        )
