from fastapi.testclient import TestClient

from app.domain.goal import GoalPriority, GoalStatus


def _create_goal(
    client: TestClient,
    headers: dict[str, str] | None = None,
    **overrides: object,
) -> object:
    payload: dict = {"title": "Ship Veyra Goals"}
    payload.update(overrides)
    return client.post("/goals", json=payload, headers=headers or {})


class TestCreateGoal:
    def test_creates_goal_with_defaults(self, client: TestClient) -> None:
        resp = _create_goal(client)
        assert resp.status_code == 201
        body = resp.json()
        assert body["title"] == "Ship Veyra Goals"
        assert body["description"] is None
        assert body["status"] == GoalStatus.ACTIVE
        assert body["priority"] == GoalPriority.MEDIUM
        assert body["target_date"] is None
        assert body["user_id"] == "dev-user"
        assert body["id"]
        assert body["created_at"]

    def test_creates_goal_with_all_fields(self, client: TestClient) -> None:
        resp = _create_goal(
            client,
            description="A long description",
            status=GoalStatus.PAUSED.value,
            priority=GoalPriority.HIGH.value,
            target_date="2026-06-01",
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["description"] == "A long description"
        assert body["status"] == GoalStatus.PAUSED.value
        assert body["priority"] == GoalPriority.HIGH.value
        assert body["target_date"] == "2026-06-01"

    def test_blank_title_rejected(self, client: TestClient) -> None:
        resp = _create_goal(client, title="   ")
        assert resp.status_code == 422

    def test_empty_title_rejected(self, client: TestClient) -> None:
        resp = _create_goal(client, title="")
        assert resp.status_code == 422

    def test_missing_title_rejected(self, client: TestClient) -> None:
        resp = _create_goal(client)
        # override to remove title
        resp = client.post("/goals", json={"description": "no title"})
        assert resp.status_code == 422

    def test_oversized_title_rejected(self, client: TestClient) -> None:
        resp = _create_goal(client, title="x" * 121)
        assert resp.status_code == 422

    def test_invalid_priority_rejected(self, client: TestClient) -> None:
        resp = _create_goal(client, priority="URGENT")
        assert resp.status_code == 422

    def test_invalid_status_rejected(self, client: TestClient) -> None:
        resp = _create_goal(client, status="DONE")
        assert resp.status_code == 422

    def test_unknown_field_rejected(self, client: TestClient) -> None:
        resp = _create_goal(client, bogus="field")
        assert resp.status_code == 422


class TestListGoals:
    def test_list_returns_created_goals(self, client: TestClient) -> None:
        _create_goal(client, title="Alpha")
        _create_goal(client, title="Beta")
        resp = client.get("/goals")
        assert resp.status_code == 200
        titles = [g["title"] for g in resp.json()]
        assert set(titles) == {"Alpha", "Beta"}

    def test_list_empty(self, client: TestClient) -> None:
        resp = client.get("/goals")
        assert resp.status_code == 200
        assert resp.json() == []


class TestGetGoal:
    def test_get_goal(self, client: TestClient) -> None:
        created = _create_goal(client, title="Fetch me").json()
        resp = client.get(f"/goals/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    def test_get_missing_goal_returns_404(self, client: TestClient) -> None:
        resp = client.get("/goals/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestUpdateGoal:
    def test_update_title_and_status(self, client: TestClient) -> None:
        created = _create_goal(client).json()
        resp = client.patch(
            f"/goals/{created['id']}",
            json={"title": "Renamed", "status": GoalStatus.COMPLETED.value},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "Renamed"
        assert body["status"] == GoalStatus.COMPLETED.value

    def test_update_preserves_unspecified_fields(self, client: TestClient) -> None:
        created = _create_goal(
            client,
            description="keep me",
            priority=GoalPriority.CRITICAL.value,
        ).json()
        resp = client.patch(f"/goals/{created['id']}", json={"title": "Only title"})
        body = resp.json()
        assert body["title"] == "Only title"
        assert body["description"] == "keep me"
        assert body["priority"] == GoalPriority.CRITICAL.value

    def test_update_missing_goal_returns_404(self, client: TestClient) -> None:
        resp = client.patch(
            "/goals/00000000-0000-0000-0000-000000000000", json={"title": "nope"}
        )
        assert resp.status_code == 404

    def test_update_blank_title_rejected(self, client: TestClient) -> None:
        created = _create_goal(client).json()
        resp = client.patch(f"/goals/{created['id']}", json={"title": "  "})
        assert resp.status_code == 422


class TestOwnership:
    def test_list_scoped_to_user(self, client: TestClient) -> None:
        _create_goal(client, title="Mine")
        other = _create_goal(
            client, title="Theirs", headers={"X-Dev-User-Id": "other-user"}
        )
        assert other.status_code == 201
        titles = [g["title"] for g in client.get("/goals").json()]
        assert titles == ["Mine"]

    def test_get_scoped_to_user(self, client: TestClient) -> None:
        created = _create_goal(client).json()
        other_resp = client.get(
            f"/goals/{created['id']}", headers={"X-Dev-User-Id": "other-user"}
        )
        assert other_resp.status_code == 404

    def test_update_scoped_to_user(self, client: TestClient) -> None:
        created = _create_goal(client).json()
        other_resp = client.patch(
            f"/goals/{created['id']}",
            json={"title": "hacked"},
            headers={"X-Dev-User-Id": "other-user"},
        )
        assert other_resp.status_code == 404

    def test_delete_scoped_to_user(self, client: TestClient) -> None:
        created = _create_goal(client).json()
        other_resp = client.delete(
            f"/goals/{created['id']}",
            headers={"X-Dev-User-Id": "other-user"},
        )
        assert other_resp.status_code == 404
        # Original user can still get the goal
        assert client.get(f"/goals/{created['id']}").status_code == 200


class TestDeleteGoal:
    def test_delete_goal_success(self, client: TestClient) -> None:
        created = _create_goal(client).json()
        del_resp = client.delete(f"/goals/{created['id']}")
        assert del_resp.status_code == 204
        get_resp = client.get(f"/goals/{created['id']}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_goal_returns_404(self, client: TestClient) -> None:
        from uuid import uuid4
        fake_id = str(uuid4())
        resp = client.delete(f"/goals/{fake_id}")
        assert resp.status_code == 404