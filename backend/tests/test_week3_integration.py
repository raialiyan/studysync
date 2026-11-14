"""API integration and authorization checks for StudySync Week 3."""
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy import select


def request(client, method, path, token=None, expected=200, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = client.request(method, path, headers=headers, **kwargs)
    assert response.status_code == expected, f"{method} {path}: {response.status_code} {response.text}"
    return response.json() if response.content else None


def new_user(client):
    email = f"week4-{uuid.uuid4().hex}@example.com"
    password = "TestPassword123!"
    request(client, "POST", "/register", expected=201, json={"email": email, "password": password})
    token = request(client, "POST", "/login", json={"email": email, "password": password})["access_token"]
    identity = request(client, "GET", "/users/me", token)["id"]
    return {"email": email, "token": token, "id": identity}


@pytest.fixture
def setup(client):
    owner, member, outsider = (new_user(client) for _ in range(3))
    ws = request(client, "POST", "/workspaces", owner["token"], expected=201, json={"name": "Week4 Test"})["id"]
    request(client, "POST", f"/workspaces/{ws}/members", owner["token"], expected=201, json={"email": member["email"]})
    module = request(client, "POST", f"/workspaces/{ws}/modules", owner["token"], expected=201, json={"name": "Testing"})["id"]
    return {"owner": owner, "member": member, "outsider": outsider, "ws": ws, "module": module}


def task(client, setup, **fields):
    return request(client, "POST", f'/modules/{setup["module"]}/tasks', setup["owner"]["token"], expected=201,
                   json={"title": "Example task", **fields})


def test_task_crud(client, setup):
    a = task(client, setup, description="Initial")
    tid = a["id"]
    assert a["status"] == "todo"
    assert any(t["id"] == tid for t in request(client, "GET", f'/modules/{setup["module"]}/tasks', setup["member"]["token"]))
    assert request(client, "GET", f"/tasks/{tid}", setup["owner"]["token"])["title"] == "Example task"
    result = request(client, "PATCH", f"/tasks/{tid}", setup["owner"]["token"], json={"title": "Edited", "status": "done", "description": None})
    assert result["title"] == "Edited" and result["status"] == "done" and result["description"] is None
    request(client, "DELETE", f"/tasks/{tid}", setup["owner"]["token"], expected=204)
    request(client, "GET", f"/tasks/{tid}", setup["owner"]["token"], expected=404)


@pytest.mark.parametrize("payload", [{"title": " "}, {"title": "x"*256}, {"title": "ok", "status": "blocked"},
                                     {"title": "ok", "description": "x"*1001}])
def test_invalid_task_creation(client, setup, payload):
    request(client, "POST", f'/modules/{setup["module"]}/tasks', setup["owner"]["token"], expected=422, json=payload)


def test_invalid_update_and_missing_ids(client, setup):
    tid = task(client, setup)["id"]
    for payload in ({"title": None}, {"title": "  "}, {"status": None}, {"status": "invalid"}):
        request(client, "PATCH", f"/tasks/{tid}", setup["owner"]["token"], expected=422, json=payload)
    request(client, "GET", "/tasks/999999", setup["owner"]["token"], expected=404)
    request(client, "GET", "/modules/999999/tasks", setup["owner"]["token"], expected=404)


def test_assignment_members_only(client, setup):
    tid = task(client, setup, assigned_to_id=setup["member"]["id"])["id"]
    assert request(client, "GET", f"/tasks/{tid}", setup["owner"]["token"])["assigned_to_id"] == setup["member"]["id"]
    request(client, "PATCH", f"/tasks/{tid}", setup["owner"]["token"], expected=422,
            json={"assigned_to_id": setup["outsider"]["id"]})
    assert request(client, "PATCH", f"/tasks/{tid}", setup["owner"]["token"], json={"assigned_to_id": None})["assigned_to_id"] is None


def test_nonmember_cannot_access_guessed_ids(client, setup):
    tid = task(client, setup)["id"]
    outsider = setup["outsider"]["token"]
    paths = [("GET", f"/tasks/{tid}"), ("PATCH", f"/tasks/{tid}"), ("DELETE", f"/tasks/{tid}"),
             ("GET", f'/modules/{setup["module"]}/tasks'), ("GET", f"/tasks/{tid}/comments"),
             ("POST", f"/tasks/{tid}/comments"), ("GET", f'/workspaces/{setup["ws"]}/activity')]
    for method, path in paths:
        request(client, method, path, outsider, expected=404, json={"title": "Unauthorized", "content": "Unauthorized"} if method in ("PATCH", "POST") else None)


def test_comments_ownership_and_validation(client, setup):
    tid = task(client, setup)["id"]
    owner, member = setup["owner"]["token"], setup["member"]["token"]
    cid = request(client, "POST", f"/tasks/{tid}/comments", member, expected=201, json={"content": " Good work "})["id"]
    comment = request(client, "GET", f"/tasks/{tid}/comments", owner)[0]
    assert comment["id"] == cid and comment["user_id"] == setup["member"]["id"] and comment["content"] == "Good work"
    request(client, "DELETE", f"/comments/{cid}", owner, expected=403)
    request(client, "DELETE", f"/comments/{cid}", setup["outsider"]["token"], expected=404)
    request(client, "POST", f"/tasks/{tid}/comments", member, expected=422, json={"content": "  "})
    request(client, "DELETE", f"/comments/{cid}", member, expected=204)
    assert request(client, "GET", f"/tasks/{tid}/comments", owner) == []


def test_activity_order_and_member_only(client, setup):
    tid = task(client, setup)["id"]
    request(client, "PATCH", f"/tasks/{tid}", setup["owner"]["token"], json={"status": "done"})
    request(client, "POST", f"/tasks/{tid}/comments", setup["member"]["token"], expected=201, json={"content": "Done"})
    feed = request(client, "GET", f'/workspaces/{setup["ws"]}/activity', setup["member"]["token"])
    assert [a["event_type"] for a in feed[:3]] == ["comment_added", "task_status_changed", "task_created"]
    assert [a["id"] for a in feed] == sorted((a["id"] for a in feed), reverse=True)
    request(client, "GET", f'/workspaces/{setup["ws"]}/activity?limit=0', setup["owner"]["token"], expected=422)
    request(client, "GET", f'/workspaces/{setup["ws"]}/activity?limit=101', setup["owner"]["token"], expected=422)
    request(client, "GET", f'/workspaces/{setup["ws"]}/activity', setup["outsider"]["token"], expected=404)


def test_cascade_task_delete_preserves_activity(client, setup):
    tid = task(client, setup)["id"]
    cid = request(client, "POST", f"/tasks/{tid}/comments", setup["owner"]["token"], expected=201, json={"content": "Note"})["id"]
    request(client, "DELETE", f"/tasks/{tid}", setup["owner"]["token"], expected=204)
    activity = request(client, "GET", f'/workspaces/{setup["ws"]}/activity', setup["owner"]["token"])
    assert any(e["event_type"] == "task_deleted" for e in activity)
    assert any(e["event_type"] == "comment_added" for e in activity)
    request(client, "DELETE", f"/comments/{cid}", setup["owner"]["token"], expected=404)


def test_workspace_delete_with_activity(client, setup):
    task(client, setup)
    request(client, "DELETE", f'/workspaces/{setup["ws"]}', setup["owner"]["token"], expected=204)
    request(client, "GET", f'/workspaces/{setup["ws"]}/activity', setup["owner"]["token"], expected=404)


def test_revoked_membership(client, setup):
    tid = task(client, setup)["id"]
    request(client, "DELETE", f'/workspaces/{setup["ws"]}/members/{setup["member"]["id"]}',
            setup["owner"]["token"], expected=204)
    request(client, "GET", f"/tasks/{tid}", setup["member"]["token"], expected=404)
    request(client, "GET", f'/workspaces/{setup["ws"]}/activity', setup["member"]["token"], expected=404)


def test_expired_token_cannot_read_task(client, setup):
    import auth
    tid = task(client, setup)["id"]
    token = jwt.encode({"sub": str(setup["owner"]["id"]), "exp": datetime.now(timezone.utc)-timedelta(minutes=1)},
                       auth.SECRET_KEY, algorithm="HS256")
    request(client, "GET", f"/tasks/{tid}", token, expected=401)
