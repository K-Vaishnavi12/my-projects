"""Unit + integration tests for auth endpoints."""


def test_register_success(client):
    resp = client.post("/api/auth/register", json={
        "email": "new@example.com",
        "username": "newuser",
        "full_name": "New User",
        "password": "securepass1",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert "hashed_password" not in data


def test_register_duplicate_email(client, registered_user):
    resp = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "username": "other",
        "full_name": "Other",
        "password": "password123",
    })
    assert resp.status_code == 409


def test_register_weak_password(client):
    resp = client.post("/api/auth/register", json={
        "email": "weak@example.com",
        "username": "weakuser",
        "full_name": "Weak",
        "password": "short",
    })
    assert resp.status_code == 422


def test_login_success(client, registered_user):
    resp = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_wrong_password(client, registered_user):
    resp = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpass",
    })
    assert resp.status_code == 401


def test_get_me(client, auth_headers):
    resp = client.get("/api/users/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"


def test_get_me_no_token(client):
    resp = client.get("/api/users/me")
    assert resp.status_code == 401


def test_password_reset_flow(client, registered_user):
    # Request reset
    resp = client.post("/api/auth/password-reset/request", json={"email": "test@example.com"})
    assert resp.status_code == 200
    token = resp.json()["reset_token"]

    # Confirm reset
    resp2 = client.post("/api/auth/password-reset/confirm", json={
        "token": token,
        "new_password": "newpassword123",
    })
    assert resp2.status_code == 200

    # Login with new password
    resp3 = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "newpassword123",
    })
    assert resp3.status_code == 200
