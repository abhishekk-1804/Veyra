import json
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.ai.provider import AIProvider, PlannedTask, PlanProposal
from app.api.routes.ai import get_ai_provider
from app.db.session import get_db
from app.main import app

def _create_goal(client: TestClient, headers: dict | None = None) -> dict:
    resp = client.post("/goals", headers=headers, json={"title": "Test Goal"})
    assert resp.status_code == 201
    return resp.json()

# 15. valid provider output
def test_valid_provider_output(client):
    goal = _create_goal(client)
    resp = client.post("/ai/plans", json={"goal_id": goal["id"], "prompt": "Make a plan"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "PENDING"
    assert len(body["proposal"]["tasks"]) == 3

# 16. malformed provider output
def test_malformed_provider_output(client):
    class MalformedProvider(AIProvider):
        def generate_plan(self, goal_title: str, goal_description: str | None, prompt: str) -> PlanProposal:
            return PlanProposal(goal_id="dummy", summary="malformed", tasks=[])
            
    app.dependency_overrides[get_ai_provider] = lambda: MalformedProvider()
    try:
        goal = _create_goal(client)
        resp = client.post("/ai/plans", json={"goal_id": goal["id"], "prompt": "test"})
        assert resp.status_code == 422
        assert "at least one task" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_ai_provider, None)

# 17. empty title
def test_empty_title_in_proposal(client):
    class EmptyTitleProvider(AIProvider):
        def generate_plan(self, goal_title: str, goal_description: str | None, prompt: str) -> PlanProposal:
            return PlanProposal(
                goal_id="dummy",
                summary="test",
                tasks=[PlannedTask(title="   ", priority="MEDIUM")]
            )
            
    app.dependency_overrides[get_ai_provider] = lambda: EmptyTitleProvider()
    try:
        goal = _create_goal(client)
        resp = client.post("/ai/plans", json={"goal_id": goal["id"], "prompt": "test"})
        assert resp.status_code == 422
        assert "blank" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_ai_provider, None)

# 18. invalid estimate
def test_invalid_estimate_in_proposal(client):
    class InvalidEstimateProvider(AIProvider):
        def generate_plan(self, goal_title: str, goal_description: str | None, prompt: str) -> PlanProposal:
            return PlanProposal(
                goal_id="dummy",
                summary="test",
                tasks=[PlannedTask(title="T1", estimated_minutes=1500, priority="MEDIUM")]
            )
            
    app.dependency_overrides[get_ai_provider] = lambda: InvalidEstimateProvider()
    try:
        goal = _create_goal(client)
        resp = client.post("/ai/plans", json={"goal_id": goal["id"], "prompt": "test"})
        assert resp.status_code == 422
        assert "estimate" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_ai_provider, None)

# 19. invalid date
def test_invalid_date_in_proposal(client):
    class InvalidDateProvider(AIProvider):
        def generate_plan(self, goal_title: str, goal_description: str | None, prompt: str) -> PlanProposal:
            return PlanProposal(
                goal_id="dummy",
                summary="test",
                tasks=[PlannedTask(title="T1", due_date="not-a-date", priority="MEDIUM")]
            )
            
    app.dependency_overrides[get_ai_provider] = lambda: InvalidDateProvider()
    try:
        goal = _create_goal(client)
        resp = client.post("/ai/plans", json={"goal_id": goal["id"], "prompt": "test"})
        assert resp.status_code == 422
        assert "due date" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_ai_provider, None)

# 20. too many tasks
def test_too_many_tasks_in_proposal(client):
    class TooManyTasksProvider(AIProvider):
        def generate_plan(self, goal_title: str, goal_description: str | None, prompt: str) -> PlanProposal:
            tasks = [PlannedTask(title=f"T{i}", priority="LOW") for i in range(16)]
            return PlanProposal(goal_id="dummy", summary="test", tasks=tasks)
            
    app.dependency_overrides[get_ai_provider] = lambda: TooManyTasksProvider()
    try:
        goal = _create_goal(client)
        resp = client.post("/ai/plans", json={"goal_id": goal["id"], "prompt": "test"})
        assert resp.status_code == 422
        assert "Too many tasks" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_ai_provider, None)

# 21. excessive total duration
def test_excessive_total_duration_in_proposal(client):
    class ExcessiveDurationProvider(AIProvider):
        def generate_plan(self, goal_title: str, goal_description: str | None, prompt: str) -> PlanProposal:
            tasks = [
                PlannedTask(title="T1", estimated_minutes=1400, priority="HIGH"),
                PlannedTask(title="T2", estimated_minutes=1400, priority="HIGH"),
                PlannedTask(title="T3", estimated_minutes=1400, priority="HIGH"),
                PlannedTask(title="T4", estimated_minutes=1000, priority="HIGH"),
            ] # sum = 5200 > 4800
            return PlanProposal(goal_id="dummy", summary="test", tasks=tasks)
            
    app.dependency_overrides[get_ai_provider] = lambda: ExcessiveDurationProvider()
    try:
        goal = _create_goal(client)
        resp = client.post("/ai/plans", json={"goal_id": goal["id"], "prompt": "test"})
        assert resp.status_code == 422
        assert "exceeds" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_ai_provider, None)

# 22. provider failure
def test_provider_failure(client):
    class FailingProvider(AIProvider):
        def generate_plan(self, goal_title: str, goal_description: str | None, prompt: str) -> PlanProposal:
            raise RuntimeError("Provider connection failed")
            
    app.dependency_overrides[get_ai_provider] = lambda: FailingProvider()
    try:
        goal = _create_goal(client)
        with pytest.raises(RuntimeError):
            client.post("/ai/plans", json={"goal_id": goal["id"], "prompt": "test"})
    finally:
        app.dependency_overrides.pop(get_ai_provider, None)

# 23. proposal persistence
def test_proposal_persistence(client):
    goal = _create_goal(client)
    resp = client.post("/ai/plans", json={"goal_id": goal["id"], "prompt": "test"})
    assert resp.status_code == 201
    proposal_id = resp.json()["id"]
    assert proposal_id

# 24. rejection creates zero tasks
def test_rejection_creates_zero_tasks(client):
    goal = _create_goal(client)
    resp = client.post("/ai/plans", json={"goal_id": goal["id"], "prompt": "test"})
    proposal_id = resp.json()["id"]

    reject_resp = client.post(f"/ai/plans/{proposal_id}/reject")
    assert reject_resp.status_code == 204

    # Verify zero tasks were created for this goal
    tasks_resp = client.get(f"/goals/{goal['id']}/tasks")
    assert tasks_resp.status_code == 200
    assert len(tasks_resp.json()) == 0

# 25. approval creates expected tasks & 26. uses TaskService/application path
def test_approval_creates_expected_tasks(client):
    goal = _create_goal(client)
    resp = client.post("/ai/plans", json={"goal_id": goal["id"], "prompt": "test"})
    proposal_id = resp.json()["id"]

    approve_resp = client.post(f"/ai/plans/{proposal_id}/approve")
    assert approve_resp.status_code == 200
    created_tasks = approve_resp.json()
    assert len(created_tasks) == 3

    # Verify persisted in database
    tasks_resp = client.get(f"/goals/{goal['id']}/tasks")
    assert tasks_resp.status_code == 200
    assert len(tasks_resp.json()) == 3

# 27. tampered proposal rejected
def test_tampered_proposal_rejected(client):
    goal = _create_goal(client)
    resp = client.post("/ai/plans", json={"goal_id": goal["id"], "prompt": "test"})
    proposal_id = resp.json()["id"]

    # Directly tamper with stored proposal payload in DB
    from uuid import UUID
    from app.models.proposal import PlanProposal
    db_gen = client.app.dependency_overrides[get_db]()
    db = next(db_gen)
    try:
        p = db.get(PlanProposal, UUID(proposal_id))
        tampered = json.loads(p.proposal_payload)
        tampered["summary"] = "TAMPERED CONTENT"
        p.proposal_payload = json.dumps(tampered)
        db.commit()
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


    approve_resp = client.post(f"/ai/plans/{proposal_id}/approve")
    assert approve_resp.status_code == 422
    assert "tampered" in approve_resp.json()["detail"]

# 28. unauthorized proposal rejected
def test_unauthorized_proposal_rejected(client):
    goal = _create_goal(client)
    resp = client.post("/ai/plans", json={"goal_id": goal["id"], "prompt": "test"})
    proposal_id = resp.json()["id"]

    resp2 = client.post(f"/ai/plans/{proposal_id}/approve", headers={"X-Dev-User-Id": "other-user"})
    assert resp2.status_code == 404

# 29. duplicate approval creates no duplicate tasks (idempotency)
def test_duplicate_approval_creates_no_duplicate_tasks(client):
    goal = _create_goal(client)
    resp = client.post("/ai/plans", json={"goal_id": goal["id"], "prompt": "test"})
    proposal_id = resp.json()["id"]

    resp1 = client.post(f"/ai/plans/{proposal_id}/approve")
    assert resp1.status_code == 200
    assert len(resp1.json()) == 3

    # Second approval
    resp2 = client.post(f"/ai/plans/{proposal_id}/approve")
    assert resp2.status_code == 200
    assert len(resp2.json()) == 0

    # Ensure still exactly 3 tasks in DB
    tasks_resp = client.get(f"/goals/{goal['id']}/tasks")
    assert len(tasks_resp.json()) == 3

# 30. already rejected proposal cannot be approved
def test_already_rejected_proposal_cannot_be_approved(client):
    goal = _create_goal(client)
    resp = client.post("/ai/plans", json={"goal_id": goal["id"], "prompt": "test"})
    proposal_id = resp.json()["id"]

    client.post(f"/ai/plans/{proposal_id}/reject")
    resp_approve = client.post(f"/ai/plans/{proposal_id}/approve")
    assert resp_approve.status_code == 422
    assert "already rejected" in resp_approve.json()["detail"]
