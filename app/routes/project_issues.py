"""Project Issues routes module.

This module provides routes for managing project-specific issues.
It includes routes for fetching, updating, and deleting issues related to projects, with
authorization enforced via JWT. Each route performs specific operations on errors or
rejections, such as resolving or deleting individual items.
"""

import traceback
from flask import jsonify, request, Response
from flask import Blueprint
from app.models import (
    fetch_issues_by_project,
    delete_issues_by_project,
    fetch_error,
    fetch_rejection,
    update_error_resolved,
    update_rejection_resolved,
    delete_error_by_id,
    delete_rejection_by_id,
    get_issue_summary
)
from app.utils.auth import TokenManager, AuthManager

token_manager = TokenManager()
auth_manager = AuthManager(token_manager)

bp = Blueprint("project_issues", __name__)


@bp.route("", methods=["GET"])
@auth_manager.authenticate
@auth_manager.authorize_project_access
def get_issues(project_uuid: str) -> Response:
    """Fetches a paginated list of issues for a specified project."""
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    handled = request.args.get("handled", None)
    time = request.args.get("time", None)
    resolved = request.args.get("resolved", None)

    try:
        data = fetch_issues_by_project(
            project_uuid, page, limit, handled, time, resolved
        )
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        print(f"Error in get_issues: {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Failed to fetch data"}), 500


@bp.route("", methods=["DELETE"])
@auth_manager.authenticate
@auth_manager.authorize_project_access
def delete_issues(project_uuid: str) -> Response:
    """Deletes all issues for a specified project."""
    try:
        success = delete_issues_by_project(project_uuid)
        if success:
            return "", 204
        else:
            return (
                jsonify({"status": "error", "message": "No issues found for project"}),
                404,
            )
    except Exception as e:
        print(f"Error in delete_issues: {e}")
        return jsonify({"status": "error", "message": "Failed to delete issues"}), 500


@bp.route("/errors/<error_uuid>", methods=["GET"])
@auth_manager.authenticate
@auth_manager.authorize_project_access
def get_error(project_uuid: str, error_uuid: str) -> Response:
    """Retrieves a specific error by its ID."""
    try:
        error = fetch_error(project_uuid, error_uuid)
        if error:
            return jsonify({"status": "success", "data": error}), 200
        else:
            return jsonify({"status": "error", "message": "Error not found"}), 404
    except Exception as e:
        print(f"Error in get_error: {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Failed to fetch error"}), 500


@bp.route("/rejections/<rejection_uuid>", methods=["GET"])
@auth_manager.authenticate
@auth_manager.authorize_project_access
def get_rejection(project_uuid: str, rejection_uuid: str) -> Response:
    """Retrieves a specific rejection by its UUID."""
    try:
        rejection = fetch_rejection(project_uuid, rejection_uuid)
        if rejection:
            return jsonify({"status": "success", "data": rejection}), 200
        else:
            return jsonify({"status": "error", "message": "Rejection not found"}), 404
    except Exception as e:
        print(f"Error in get_rejection: {e}")
        return jsonify({"message": "Failed to retrieve rejection"}), 500


@bp.route("/errors/<error_uuid>", methods=["PATCH"])
@auth_manager.authenticate
@auth_manager.authorize_project_access
def toggle_error(project_uuid: str, error_uuid: str) -> Response:
    """Toggles the resolved state of a specific error."""
    data = request.get_json()
    new_resolved_state = data.get("resolved")

    if new_resolved_state is None:
        return jsonify({"status": "error", "message": "Missing resolved state"}), 400

    try:
        success = update_error_resolved(error_uuid, new_resolved_state)
        if success:
            return "", 204
        else:
            return jsonify({"status": "error", "message": "Error not found"}), 404
    except Exception as e:
        print(f"Error in toggle_error: {e}")
        return (
            jsonify({"status": "error", "message": "Failed to update error state"}),
            500,
        )


@bp.route("/rejections/<rejection_uuid>", methods=["PATCH"])
@auth_manager.authenticate
@auth_manager.authorize_project_access
def toggle_rejection(project_uuid: str, rejection_uuid: str) -> Response:
    """Toggles the resolved state of a specific rejection."""
    data = request.get_json()
    new_resolved_state = data.get("resolved")

    if new_resolved_state is None:
        return jsonify({"status": "error", "message": "Missing resolved state"}), 400

    try:
        success = update_rejection_resolved(rejection_uuid, new_resolved_state)
        if success:
            return "", 204
        else:
            return jsonify({"status": "error", "message": "Rejection not found"}), 404
    except Exception as e:
        print(f"Error in toggle_rejection: {e}")
        return (
            jsonify({"status": "error", "message": "Failed to update error state"}),
            500,
        )


@bp.route("/errors/<error_uuid>", methods=["DELETE"])
@auth_manager.authenticate
@auth_manager.authorize_project_access
def delete_error(project_uuid: str, error_uuid: str) -> Response:
    """Deletes a specific error by its UUID."""
    try:
        success = delete_error_by_id(error_uuid)
        if success:
            return "", 204
        else:
            return jsonify({"status": "error", "message": "Error not found"}), 404
    except Exception as e:
        print(f"Error in delete_error: {e}")
        return jsonify({"status": "error", "message": "Failed to delete error"}), 500


@bp.route("/rejections/<rejection_uuid>", methods=["DELETE"])
@auth_manager.authenticate
@auth_manager.authorize_project_access
def delete_rejection(project_uuid: str, rejection_uuid: str) -> Response:
    """Deletes a specific rejection by its UUID."""
    try:
        success = delete_rejection_by_id(rejection_uuid)
        if success:
            return "", 204
        else:
            return jsonify({"status": "error", "message": "Rejection not found"}), 404
    except Exception as e:
        print(f"Error in delete_rejection: {e}")
        return (
            jsonify({"status": "error", "message": "Failed to delete rejection"}),
            500,
        )

@bp.route("/summary", methods=["GET"])
@auth_manager.authenticate
@auth_manager.authorize_project_access
def get_summary(project_uuid: str) -> Response:
    """Gets issue count per hour for today for this project."""
    try:
        daily_counts = get_issue_summary(project_uuid)
        return jsonify({"status": "success", "data": daily_counts}), 200
    except Exception as e:
        print(f"Error in get_summary: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch hourly summary"}), 500