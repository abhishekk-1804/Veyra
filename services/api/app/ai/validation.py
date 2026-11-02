from datetime import datetime
from app.ai.provider import PlanProposal

MAX_TASKS_PER_PROPOSAL = 15
MAX_TOTAL_ESTIMATED_MINUTES = 4800
MAX_TITLE_LENGTH = 200
MAX_NOTES_LENGTH = 2000

def validate_proposal(raw_proposal: PlanProposal) -> PlanProposal:
    if len(raw_proposal.tasks) > MAX_TASKS_PER_PROPOSAL:
        raise ValueError(f"Too many tasks. Max is {MAX_TASKS_PER_PROPOSAL}")
    if len(raw_proposal.tasks) == 0:
        raise ValueError("Proposal must contain at least one task")
    
    total_minutes = 0
    valid_priorities = {"LOW", "MEDIUM", "HIGH", "URGENT"}
    
    for task in raw_proposal.tasks:
        if not task.title or not task.title.strip():
            raise ValueError("Task title cannot be blank")
        if len(task.title.strip()) > MAX_TITLE_LENGTH:
            raise ValueError(f"Task title exceeds max length of {MAX_TITLE_LENGTH}")
            
        if task.notes and len(task.notes) > MAX_NOTES_LENGTH:
            raise ValueError(f"Task notes exceed max length of {MAX_NOTES_LENGTH}")
        
        if task.estimated_minutes is not None:
            if task.estimated_minutes <= 0 or task.estimated_minutes > 1440:
                raise ValueError("Task estimate must be between 1 and 1440 minutes")
            total_minutes += task.estimated_minutes
            
        if task.priority not in valid_priorities:
            raise ValueError(f"Invalid priority: {task.priority}")
            
        if task.due_date:
            try:
                datetime.fromisoformat(task.due_date.replace("Z", "+00:00"))
            except Exception:
                raise ValueError(f"Invalid due date format: {task.due_date}")
            
    if total_minutes > MAX_TOTAL_ESTIMATED_MINUTES:
        raise ValueError(f"Total estimated minutes exceeds {MAX_TOTAL_ESTIMATED_MINUTES}")
        
    return raw_proposal

