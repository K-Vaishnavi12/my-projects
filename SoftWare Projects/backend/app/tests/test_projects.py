"""Integration tests for project and board management."""


def test_create_project(client, auth_headers):
    resp = client.post("/api/projects", json={"name": "My Project"}, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Project"
    assert len(data["members"]) == 1  # owner auto-added


def test_list_projects(client, auth_headers):
    client.post("/api/projects", json={"name": "P1"}, headers=auth_headers)
    client.post("/api/projects", json={"name": "P2"}, headers=auth_headers)
    resp = client.get("/api/projects", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_update_project(client, auth_headers):
    proj = client.post("/api/projects", json={"name": "Old"}, headers=auth_headers).json()
    resp = client.patch(f"/api/projects/{proj['id']}", json={"name": "New"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"


def test_delete_project(client, auth_headers):
    proj = client.post("/api/projects", json={"name": "ToDelete"}, headers=auth_headers).json()
    resp = client.delete(f"/api/projects/{proj['id']}", headers=auth_headers)
    assert resp.status_code == 204


def test_create_board_with_default_columns(client, auth_headers):
    proj = client.post("/api/projects", json={"name": "BoardProj"}, headers=auth_headers).json()
    resp = client.post(
        f"/api/projects/{proj['id']}/boards",
        json={"name": "Sprint 1"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["columns"]) == 3
    col_names = [c["name"] for c in data["columns"]]
    assert "To Do" in col_names
    assert "In Progress" in col_names
    assert "Done" in col_names


def test_create_task(client, auth_headers):
    proj = client.post("/api/projects", json={"name": "P"}, headers=auth_headers).json()
    board = client.post(
        f"/api/projects/{proj['id']}/boards", json={"name": "B"}, headers=auth_headers
    ).json()
    col_id = board["columns"][0]["id"]

    resp = client.post(
        f"/api/columns/{col_id}/tasks",
        json={"title": "First task", "priority": "high"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["title"] == "First task"


def test_move_task(client, auth_headers):
    proj = client.post("/api/projects", json={"name": "P"}, headers=auth_headers).json()
    board = client.post(
        f"/api/projects/{proj['id']}/boards", json={"name": "B"}, headers=auth_headers
    ).json()
    todo_col = board["columns"][0]["id"]
    inprog_col = board["columns"][1]["id"]

    task = client.post(
        f"/api/columns/{todo_col}/tasks",
        json={"title": "Move me"},
        headers=auth_headers,
    ).json()

    resp = client.post(
        f"/api/tasks/{task['id']}/move",
        json={"column_id": inprog_col, "position": 0},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["column_id"] == inprog_col


def test_task_comment(client, auth_headers):
    proj = client.post("/api/projects", json={"name": "P"}, headers=auth_headers).json()
    board = client.post(
        f"/api/projects/{proj['id']}/boards", json={"name": "B"}, headers=auth_headers
    ).json()
    col_id = board["columns"][0]["id"]
    task = client.post(
        f"/api/columns/{col_id}/tasks", json={"title": "T"}, headers=auth_headers
    ).json()

    resp = client.post(
        f"/api/tasks/{task['id']}/comments",
        json={"content": "Great task!"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["content"] == "Great task!"
