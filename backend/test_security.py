
import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://127.0.0.1:8000"
PASSWORD = "SecurityTest123!"
SECRET_KEY = os.environ["JWT_SECRET_KEY"]


def request(method, path, expected, token=None, **kwargs):
    headers = kwargs.pop("headers", {})

    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.request(
        method,
        BASE_URL + path,
        headers=headers,
        timeout=15,
        **kwargs
    )

    assert response.status_code == expected, (
        f"{method} {path}: expected {expected}, "
        f"received {response.status_code}: {response.text}"
    )

    return response.json() if response.content else None


def register_and_login():
    email = f"security-{uuid.uuid4().hex}@example.com"

    request(
        "POST", "/register", 201,
        json={"email": email, "password": PASSWORD}
    )

    login = request(
        "POST", "/login", 200,
        json={"email": email, "password": PASSWORD}
    )

    return email, login["access_token"]


def run():
    print("Starting Week 2 security tests...")

    owner_email, owner_token = register_and_login()
    member_email, member_token = register_and_login()
    _, outsider_token = register_and_login()

    # Authentication tests
    request("GET", "/users/me", 401)

    request(
        "GET", "/users/me", 401,
        token="invalid.jwt.token"
    )

    expired_token = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc)
                   - timedelta(minutes=5)
        },
        SECRET_KEY,
        algorithm="HS256"
    )

    request("GET", "/users/me", 401, token=expired_token)

    print("PASS: Missing, invalid and expired tokens")

    # Owner creates a workspace
    workspace = request(
        "POST", "/workspaces", 201, owner_token,
        json={"name": "Security Test Workspace"}
    )

    workspace_id = workspace["id"]

    try:
        # An outsider cannot access this workspace
        request(
            "GET", f"/workspaces/{workspace_id}",
            404, outsider_token
        )

        request(
            "GET", f"/workspaces/{workspace_id}/modules",
            404, outsider_token
        )

        print("PASS: Non-members cannot access workspaces")

        # The owner adds another member
        request(
            "POST",
            f"/workspaces/{workspace_id}/members",
            201,
            owner_token,
            json={"email": member_email}
        )

        # A duplicate membership is rejected
        request(
            "POST",
            f"/workspaces/{workspace_id}/members",
            409,
            owner_token,
            json={"email": member_email}
        )

        print("PASS: Membership and duplicate checks")

        # A member cannot rename or delete the workspace
        request(
            "PATCH", f"/workspaces/{workspace_id}",
            403, member_token,
            json={"name": "Unauthorized Rename"}
        )

        request(
            "DELETE", f"/workspaces/{workspace_id}",
            403, member_token
        )

        # A member cannot add other members
        request(
            "POST",
            f"/workspaces/{workspace_id}/members",
            403,
            member_token,
            json={"email": owner_email}
        )

        # A member can create modules
        module = request(
            "POST",
            f"/workspaces/{workspace_id}/modules",
            201,
            member_token,
            json={"name": "Shared Module"}
        )

        module_id = module["id"]

        # An outsider cannot modify the module
        request(
            "PATCH", f"/modules/{module_id}",
            404, outsider_token,
            json={"name": "Unauthorized Update"}
        )

        print("PASS: Owner/Member permissions")

        # The owner removes the member
        member_details = request(
            "GET",
            f"/workspaces/{workspace_id}/members",
            200,
            owner_token
        )

        member_id = next(
            m["user_id"] for m in member_details
            if m["email"] == member_email
        )

        request(
            "DELETE",
            f"/workspaces/{workspace_id}/members/{member_id}",
            204,
            owner_token
        )

        # Removed members lose access
        request(
            "GET",
            f"/workspaces/{workspace_id}",
            404,
            member_token
        )

        print("PASS: Removed members lose access")

    finally:
        # Clean up the temporary workspace
        request(
            "DELETE",
            f"/workspaces/{workspace_id}",
            204,
            owner_token
        )

    print()
    print("ALL WEEK 2 SECURITY TESTS PASSED")


if __name__ == "__main__":
    run()
