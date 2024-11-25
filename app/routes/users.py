"""Users routes module.

This module provides routes for managing user accounts, including creating new users,
fetching all users, deleting users, and updating user passwords. Each route enforces
root access authorization, except for password updates, which require user session
authentication.
"""

import bcrypt
from flask import jsonify, request, Response
from flask import Blueprint
from app.models import (
    fetch_all_users,
    add_user,
    delete_user_by_id,
    update_password,
    fetch_projects_for_user,
    fetch_projects
)
from app.utils import is_valid_email
from app.models import user_is_root
from app.routes.projects import get_projects
from app.utils.auth import TokenManager, AuthManager

token_manager = TokenManager()
auth_manager = AuthManager(token_manager)

bp = Blueprint("users", __name__)


@bp.route("", methods=["GET"])
@auth_manager.authenticate
@auth_manager.authorize_root
def get_users() -> Response:
    """Fetches a list of all users."""
    users = fetch_all_users()
    return jsonify({"result": "success", "payload": users}), 200


@bp.route("", methods=["POST"])
@auth_manager.authenticate
@auth_manager.authorize_root
def create_user() -> Response:
    """Creates a new user with specified attributes."""
    data = request.json

    if not data: 
        return jsonify({"result": "error", "message": "Invalid request"}), 400
    
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")
    password = data.get("password")
    confirmed_password = data.get("confirmed_password")

    if (
        not email
        or not password
        or not confirmed_password
        or not first_name
        or not last_name
    ):
        return (
            jsonify({"result": "error", "message": "Missing input data"}),
            400,
        )

    if password != confirmed_password:
        return jsonify({"result": "error", "message": "Passwords do not match"}), 400

    if not is_valid_email(email):
        return jsonify({"result": "error", "message": "Invalid email format"}), 400

    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode("utf-8"), salt)

    uuid = add_user(first_name, last_name, email, password_hash.decode("utf-8"))
    user_info = {"uuid": uuid, "first_name": first_name, "last_name": last_name}
    return (
        jsonify({"result": "success", "payload": user_info}),
        201,
    )


@bp.route("/<user_uuid>", methods=["DELETE"])
@auth_manager.authenticate
@auth_manager.authorize_root
def delete_user(user_uuid: str) -> Response:
    """Deletes a specified user by their user ID."""
    success = delete_user_by_id(user_uuid)
    if success:
        return "", 204
    else:
        return jsonify({"result": "error", "message": "User not found"}), 404

@bp.route("/<user_uuid>", methods=["PATCH"])
@auth_manager.authenticate
@auth_manager.authorize_user
def update_user_password(user_uuid: str) -> Response:
    """Updates the password of a specified user."""
    data = request.json
    new_password = data.get("password")

    if not new_password:
        return jsonify({"result": "error", "message": "Missing password"}), 400

    password_hash = bcrypt.hashpw(
        new_password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    success = update_password(user_uuid, password_hash)
    if success:
        return "", 204
    else:
        return jsonify({"result": "error", "message": "User not found"}), 404


@bp.route("/<user_uuid>/projects", methods=["GET"])
@auth_manager.authenticate
@auth_manager.authorize_user
def get_user_projects(user_uuid: str) -> Response:
    """Retrieves all projects assigned to a specific user by user ID."""
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)

    if page < 1 or limit < 1:
        return jsonify({"result": "error", "message": "Invalid pagination parameters"}), 400

    user_uuid_in_path_is_for_root_user = user_is_root(user_uuid)

    if user_uuid_in_path_is_for_root_user:
        project_data = fetch_projects(page, limit)
    else: 
        project_data = fetch_projects_for_user(user_uuid, page, limit)
    
    return jsonify({"result": "success", "payload": project_data}), 200
