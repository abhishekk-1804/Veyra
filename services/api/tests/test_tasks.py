import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

def _create_goal(client: TestClient, headers: dict | None = None) -> dict:
    resp = client.post("/goals", headers=headers, json={"title": "Test Goal"})
    assert resp.status_code == 201
    return resp.json()

def test_create_task_valid(client):
    goal = _create_goal(client)
    payload = {"goal_id": goal["id"], "title": "Valid Task"}
    resp = client.post(f"/goals/{goal['id']}/tasks", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Valid Task"
    assert data["goal_id"] == goal["id"]

def test_create_task_blank_title(client):
    goal = _create_goal(client)
    payload = {"goal_id": goal["id"], "title": "   "}
    resp = client.post(f"/goals/{goal['id']}/tasks", json=payload)
    assert resp.status_code == 422

def test_create_task_oversized_title(client):
    goal = _create_goal(client)
    payload = {"goal_id": goal["id"], "title": "A" * 201}
    resp = client.post(f"/goals/{goal['id']}/tasks", json=payload)
    assert resp.status_code == 422

def test_create_task_invalid_goal(client):
    fake_id = str(uuid4())
    payload = {"goal_id": fake_id, "title": "Valid Task"}
    resp = client.post(f"/goals/{fake_id}/tasks", json=payload)
    assert resp.status_code == 404

def test_create_task_invalid_estimate_zero(client):
    goal = _create_goal(client)
    payload = {"goal_id": goal["id"], "title": "T", "estimated_minutes": 0}
    resp = client.post(f"/goals/{goal['id']}/tasks", json=payload)
    assert resp.status_code == 422

def test_create_task_invalid_estimate_negative(client):
    goal = _create_goal(client)
    payload = {"goal_id": goal["id"], "title": "T", "estimated_minutes": -10}
    resp = client.post(f"/goals/{goal['id']}/tasks", json=payload)
    assert resp.status_code == 422

def test_create_task_invalid_estimate_too_large(client):
    goal = _create_goal(client)
    payload = {"goal_id": goal["id"], "title": "T", "estimated_minutes": 1500}
    resp = client.post(f"/goals/{goal['id']}/tasks", json=payload)
    assert resp.status_code == 422

def test_create_task_invalid_date_rejected(client):
    goal = _create_goal(client)
    payload = {"goal_id": goal["id"], "title": "T", "due_date": "invalid-datetime-string"}
    resp = client.post(f"/goals/{goal['id']}/tasks", json=payload)
    assert resp.status_code == 422


def test_get_task(client):
    goal = _create_goal(client)
    payload = {"goal_id": goal["id"], "title": "T"}
    resp = client.post(f"/goals/{goal['id']}/tasks", json=payload)
    task_id = resp.json()["id"]

    resp2 = client.get(f"/tasks/{task_id}")
    assert resp2.status_code == 200
    assert resp2.json()["id"] == task_id

def test_list_tasks(client):
    goal = _create_goal(client)
    client.post(f"/goals/{goal['id']}/tasks", json={"goal_id": goal["id"], "title": "T1"})
    client.post(f"/goals/{goal['id']}/tasks", json={"goal_id": goal["id"], "title": "T2"})

    resp = client.get(f"/goals/{goal['id']}/tasks")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

def test_update_task(client):
    goal = _create_goal(client)
    resp = client.post(f"/goals/{goal['id']}/tasks", json={"goal_id": goal["id"], "title": "T1"})
    task_id = resp.json()["id"]

    resp2 = client.patch(f"/tasks/{task_id}", json={"title": "T2"})
    assert resp2.status_code == 200
    assert resp2.json()["title"] == "T2"

def test_update_task_status_transition(client):
    goal = _create_goal(client)
    resp = client.post(f"/goals/{goal['id']}/tasks", json={"goal_id": goal["id"], "title": "T1"})
    task_id = resp.json()["id"]

    resp2 = client.patch(f"/tasks/{task_id}", json={"status": "IN_PROGRESS"})
    assert resp2.status_code == 200

def test_update_task_invalid_status_transition(client):
    goal = _create_goal(client)
    resp = client.post(f"/goals/{goal['id']}/tasks", json={"goal_id": goal["id"], "title": "T1"})
    task_id = resp.json()["id"]
    
    client.patch(f"/tasks/{task_id}", json={"status": "COMPLETED"})
    
    resp2 = client.patch(f"/tasks/{task_id}", json={"status": "IN_PROGRESS"})
    assert resp2.status_code == 422

def test_delete_task(client):
    goal = _create_goal(client)
    resp = client.post(f"/goals/{goal['id']}/tasks", json={"goal_id": goal["id"], "title": "T1"})
    task_id = resp.json()["id"]

    resp2 = client.delete(f"/tasks/{task_id}")
    assert resp2.status_code == 204
    
    resp3 = client.get(f"/tasks/{task_id}")
    assert resp3.status_code == 404

def test_task_isolation(client):
    goal = _create_goal(client)
    resp = client.post(f"/goals/{goal['id']}/tasks", json={"goal_id": goal["id"], "title": "T1"})
    task_id = resp.json()["id"]

    resp2 = client.get(f"/tasks/{task_id}", headers={"X-Dev-User-Id": "other"})
    assert resp2.status_code == 404

def test_get_nonexistent_task(client):
    fake_id = str(uuid4())
    resp = client.get(f"/tasks/{fake_id}")
    assert resp.status_code == 404

def test_get_tasks_nonexistent_goal(client):
    fake_id = str(uuid4())
    resp = client.get(f"/goals/{fake_id}/tasks")
    assert resp.status_code == 404

def test_create_task_oversized_description(client):
    goal = _create_goal(client)
    payload = {"goal_id": goal["id"], "title": "T", "description": "A" * 2001}
    resp = client.post(f"/goals/{goal['id']}/tasks", json=payload)
    assert resp.status_code == 422

def test_due_date_field(client):
    goal = _create_goal(client)
    payload = {"goal_id": goal["id"], "title": "T", "due_date": "2030-01-01T00:00:00Z"}
    resp = client.post(f"/goals/{goal['id']}/tasks", json=payload)
    assert resp.status_code == 201
    assert resp.json()["due_date"] is not None

def test_cross_user_goal_access_prevented(client):
    goal = _create_goal(client)
    payload = {"goal_id": goal["id"], "title": "T"}
    resp = client.post(f"/goals/{goal['id']}/tasks", headers={"X-Dev-User-Id": "other"}, json=payload)
    assert resp.status_code == 404
