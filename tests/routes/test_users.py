from unittest.mock import patch
from tests.mock_data import raw_users

def test_get_users(root_client, regular_user):
    """Test fetching all users as a root user."""
    response = root_client.get("/api/users")

    assert response.status_code == 200
    assert "payload" in response.json, "Response should contain 'payload' key."
    assert len(response.json["payload"]) == 2, "There should be two users returned."
    emails = [user["email"] for user in response.json["payload"]]
    assert "admin@admin.com" in emails
    assert "john@doe.com" in emails


def test_create_user(root_client):
    new_user_data = raw_users["new_user"]

    response = root_client.post("/api/users", json=new_user_data)

    assert response.status_code == 201
    assert "payload" in response.json, "Response should contain 'payload' key."
    assert response.json["payload"]["email"] == "jane@smith.com"
    assert response.json["payload"]["is_root"] is False


def test_get_session_info(root_client):
    response = root_client.get("/api/users/me")

    assert response.status_code == 200
    assert "payload" in response.json, "Response should contain 'payload' key."
    assert response.json["payload"]["email"] == "admin@admin.com"
    assert response.json["payload"]["is_root"] is True


def test_delete_user(root_client, regular_user, test_db):
    user_uuid = regular_user[0]
    response = root_client.delete(f"/api/users/{user_uuid}")

    assert response.status_code == 204

    # Verify the user was deleted from the database
    test_db.execute("SELECT * FROM users WHERE uuid = %s;", (user_uuid,))
    assert test_db.fetchone() is None, "User should be deleted from the database."


def test_update_user_password(regular_client, regular_user, test_db):
    """Test updating the password for a regular user."""
    user_uuid = regular_user[0]
    new_password_data = {"password": "newsecurepassword"}

    test_db.execute("SELECT password_hash FROM users WHERE uuid = %s;", (user_uuid,))
    old_password_hash = test_db.fetchone()[0]
    assert old_password_hash is not None, "Old password hash should exist."

    response = regular_client.patch(f"/api/users/{user_uuid}", json=new_password_data)

    assert response.status_code == 204

    # Verify the password was updated in the database 
    test_db.execute("SELECT password_hash FROM users WHERE uuid = %s;", (user_uuid,))
    updated_password_hash = test_db.fetchone()[0]
    assert updated_password_hash is not None, "Updated password hash should exist."

    # Compare the hashes
    assert old_password_hash != updated_password_hash, "Password hash should be updated."


def test_get_user_projects(regular_client, regular_user, projects, user_project_assignment):
    """Test fetching projects assigned to a regular user."""
    user_uuid = regular_user[0]
    response = regular_client.get(f"/api/users/{user_uuid}/projects")

    assert response.status_code == 200
    assert "payload" in response.json, "Response should contain 'payload' key."
    assert "projects" in response.json["payload"], "Response payload should contain 'projects' key."
    fetched_projects = response.json["payload"]["projects"]
    assert len(fetched_projects) == 1
    assert fetched_projects[0]["name"] == projects[0]["name"]