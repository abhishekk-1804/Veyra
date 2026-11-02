from datetime import datetime, timedelta, timezone
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient


def _create_goal(client: TestClient, headers: dict | None = None) -> dict:
    resp = client.post("/goals", headers=headers, json={"title": "Test Goal"})
    assert resp.status_code == 201
    return resp.json()


def _create_task(client: TestClient, goal_id: str, title: str, **kwargs) -> dict:
    payload = {"goal_id": goal_id, "title": title, **kwargs}
    resp = client.post(f"/goals/{goal_id}/tasks", json=payload)
    assert resp.status_code == 201
    return resp.json()


# 1. Overdue detection
def test_replan_overdue_detection(client: TestClient):
    goal = _create_goal(client)
    past_due = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    t = _create_task(client, goal["id"], "Overdue Task", due_date=past_due)

    replan_resp = client.post(f"/goals/{goal['id']}/replan", json={})
    assert replan_resp.status_code == 200
    data = replan_resp.json()
    assert len(data["adjustments"]) == 1
    adj = data["adjustments"][0]
    assert adj["task_id"] == t["id"]
    assert adj["trigger"] == "OVERDUE"
    assert adj["action"] == "ESCALATE_PRIORITY"


# 2. Deferred task handling
def test_replan_deferred_task_handling(client: TestClient):
    goal = _create_goal(client)
    _create_task(client, goal["id"], "Task 1", estimated_minutes=80, priority="HIGH")
    t2 = _create_task(client, goal["id"], "Task 2", estimated_minutes=80, priority="LOW")

    # In a 100m window, Task 2 is deferred
    replan_resp = client.post(
        f"/goals/{goal['id']}/replan",
        json={"available_minutes": 100},
    )
    assert replan_resp.status_code == 200
    data = replan_resp.json()
    deferred_adjs = [a for a in data["adjustments"] if a["trigger"] == "DEFERRED"]
    assert len(deferred_adjs) >= 1
    assert any(a["task_id"] == t2["id"] for a in deferred_adjs)


# 3. Cancellation handling
def test_replan_cancellation_handling(client: TestClient):
    goal = _create_goal(client)
    t = _create_task(client, goal["id"], "Cancelled Task")
    client.patch(f"/tasks/{t['id']}", json={"status": "CANCELLED"})

    replan_resp = client.post(f"/goals/{goal['id']}/replan", json={})
    assert replan_resp.status_code == 200
    data = replan_resp.json()
    cancelled_adjs = [a for a in data["adjustments"] if a["trigger"] == "CANCELLED"]
    assert len(cancelled_adjs) == 1
    assert cancelled_adjs[0]["task_id"] == t["id"]


# 4. Proposal generation does NOT silently mutate state
def test_replan_proposal_generation_never_mutates_state(client: TestClient):
    goal = _create_goal(client)
    past_due = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    t = _create_task(client, goal["id"], "Overdue Task", due_date=past_due, priority="LOW")

    # Generate proposal
    replan_resp = client.post(f"/goals/{goal['id']}/replan", json={})
    assert replan_resp.status_code == 200

    # Verify task state is completely unchanged in the database
    t_after = client.get(f"/tasks/{t['id']}").json()
    assert t_after["priority"] == "LOW"
    assert t_after["status"] == "TODO"


# 5. Approval boundary: applying adjustment updates task
def test_replan_apply_adjustment(client: TestClient):
    goal = _create_goal(client)
    past_due = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    t = _create_task(client, goal["id"], "Overdue Task", due_date=past_due, priority="LOW")

    # Apply approved adjustment
    apply_resp = client.post(
        f"/goals/{goal['id']}/replan/apply",
        json={"task_id": t["id"], "action": "ESCALATE_PRIORITY"},
    )
    assert apply_resp.status_code == 200
    updated_task = apply_resp.json()
    assert updated_task["priority"] == "URGENT"

    # Verify persisted in database
    t_after = client.get(f"/tasks/{t['id']}").json()
    assert t_after["priority"] == "URGENT"


# 6. Ownership isolation on replan and apply
def test_replan_ownership_isolation(client: TestClient):
    goal = _create_goal(client)
    t = _create_task(client, goal["id"], "Task 1")

    # Other user cannot request replan for goal
    replan_other = client.post(
        f"/goals/{goal['id']}/replan",
        headers={"X-Dev-User-Id": "other-user"},
        json={},
    )
    assert replan_other.status_code == 404

    # Other user cannot apply replan
    apply_other = client.post(
        f"/goals/{goal['id']}/replan/apply",
        headers={"X-Dev-User-Id": "other-user"},
        json={"task_id": t["id"], "action": "ESCALATE_PRIORITY"},
    )
    assert apply_other.status_code == 404
