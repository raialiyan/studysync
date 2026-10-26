
import requests

BASE = "http://127.0.0.1:8000"
EMAIL = "week2test@example.com"
PASSWORD = "TestPassword123!"


def call(method, path, expected, token=None, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.request(
        method, BASE + path,
        headers=headers,
        timeout=15,
        **kwargs
    )

    assert response.status_code == expected, (
        f"{method} {path}: expected {expected}, "
        f"got {response.status_code}: {response.text}"
    )

    return response.json() if response.content else None


def run():
    # Register, or continue with an existing test account
    r = requests.post(
        BASE + "/register",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=15
    )
    assert r.status_code in (201, 400), r.text

    login = call(
        "POST", "/login", 200,
        json={"email": EMAIL, "password": PASSWORD}
    )
    token = login["access_token"]

    call("GET", "/users/me", 200, token=token)
    call("GET", "/workspaces", 401)

    workspace = call(
        "POST", "/workspaces", 201, token,
        json={"name": "Week 2 Test Workspace"}
    )
    wid = workspace["id"]

    call("GET", "/workspaces", 200, token)
    call("GET", f"/workspaces/{wid}", 200, token)

    call(
        "PATCH", f"/workspaces/{wid}", 200, token,
        json={"name": "Updated Workspace"}
    )

    members = call(
        "GET", f"/workspaces/{wid}/members", 200, token
    )
    assert len(members) == 1
    assert members[0]["role"] == "owner"

    module = call(
        "POST", f"/workspaces/{wid}/modules", 201, token,
        json={"name": "Machine Learning"}
    )
    mid = module["id"]

    call("GET", f"/workspaces/{wid}/modules", 200, token)

    call(
        "PATCH", f"/modules/{mid}", 200, token,
        json={"name": "Advanced ML"}
    )

    call("DELETE", f"/modules/{mid}", 204, token)
    call("DELETE", f"/workspaces/{wid}", 204, token)

    print("ALL BASIC WEEK 2 BACKEND TESTS PASSED")


if __name__ == "__main__":
    run()
