import jwt
import json
from flask import request, jsonify, Response
from typing import Any
from functools import wraps
from app.models import fetch_project_users
from .auth_helpers import refresh_token


class JWTAuth:
    def __init__(self, secret_key: str) -> None:
        self.secret_key = secret_key

    def _get_token(self) -> str | None:
        auth_header = request.headers.get("Authorization")
        if auth_header and len(auth_header.split(" ")) == 2:
            return auth_header.split(" ")[1]  # Assuming "Bearer <token>"
        return None

    def _decode_token(self, token: str) -> dict:
        return jwt.decode(token, self.secret_key, algorithms=["HS256"])

    def authorize_user_for_project(
        self, f: callable, token: str, *args: tuple, **kwargs: dict
    ) -> Response | Any:
        decoded_token = self._decode_token(token)
        user_id = decoded_token.get("user_id")
        project_pid = kwargs.get("pid")

        if project_pid:
            authorized_user_ids = fetch_project_users(project_pid)
            if not authorized_user_ids:
                return (
                    jsonify({"message": "Project was not found or has no users"}),
                    404,
                )
            if user_id not in authorized_user_ids:
                print("user", user_id, authorized_user_ids)
                return jsonify({"message": "Unauthorized for this project"}), 403

        return f(*args, **kwargs)

    def handle_expired_access_token(
        self, f: callable, *args: tuple, **kwargs: dict
    ) -> Response:
        # error-handling is built-in in the refresh_token method definition
        parsed_json_data = json.loads(refresh_token()[0].get_data().decode("utf-8"))
        new_access_token = parsed_json_data.get("access_token")

        if new_access_token:
            try:
                return self.authorize_user_for_project(
                    f, new_access_token, *args, **kwargs
                )
            except jwt.ExpiredSignatureError:
                return self.handle_expired_access_token(f, *args, **kwargs)
            except jwt.InvalidTokenError:
                return jsonify({"message": "Invalid token."}), 401
        else:
            # return message for invalid or expired refresh token
            return parsed_json_data

    def check_session_and_authorization(self, f: callable) -> callable:
        @wraps(f)
        def decorated_function(*args: tuple, **kwargs: dict) -> Response:
            token = self._get_token()
            if not token:
                return jsonify({"message": "Token is missing!"}), 401

            try:
                return self.authorize_user_for_project(f, token, *args, **kwargs)
            except jwt.ExpiredSignatureError:
                return self.handle_expired_access_token(f, *args, **kwargs)
            except jwt.InvalidTokenError:
                return jsonify({"message": "Invalid token."}), 401

        return decorated_function