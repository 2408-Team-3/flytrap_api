"""JWT Authentication utility.

This module provides the `JWTAuth` class, which handles JWT-based authentication and
authorization. The class includes methods for token validation, user authorization for
projects, and handling expired tokens by refreshing access tokens as needed.
This functionality is applied as decorators to routes that require authentication.

Classes:
    JWTAuth: Manages JWT-based authentication and authorization for project access.

Usage:
    jwt_auth = JWTAuth(secret_key="your_secret_key")
"""

import jwt
import json
from flask import request, jsonify, make_response, Response
from typing import Any
from functools import wraps
from app.models import fetch_project_users, get_user_root_info
from .get_new_access_token import get_new_access_token


class JWTAuth:
    """A class to manage JWT-based authentication and authorization.

    This class provides methods to validate and decode tokens, authorize users for
    specific projects, handle expired tokens by refreshing them, and apply
    authentication as decorators to routes.

    Attributes:
        secret_key (str): The secret key used to encode and decode JWT tokens.
    """

    def __init__(self, secret_key: str) -> None:
        """Initializes the JWTAuth class with a secret key for encoding and decoding
        tokens.

        Args:
            secret_key (str): The secret key for JWT token operations.
        """
        self.secret_key = secret_key
    
    def check_session_and_authorization(self, root_required: bool = False) -> callable:
        """Decorator factory to check JWT session token validity and user authorization.

        Args:
            f (callable): The function to wrap with session and authorization checks.

        Returns:
            callable: The wrapped function with added session and authorization checks.
        """

        def decorator(f: callable) -> callable:
            @wraps(f)
            def decorated_function(
                new_access_token=None, *args: tuple, **kwargs: dict
            ) -> Response:                
                try:
                    if new_access_token:
                        token = new_access_token
                    else:
                        token = self._get_token()

                    if not token:
                        return jsonify({"message": "Token is missing"}), 401

                    if root_required:
                        return self._authenticate_root(f, token, *args, **kwargs)
                    
                    if 'project_uuid' in kwargs:
                        return self.authorize_user_for_project(f, token, *args, **kwargs)
                    elif 'user_uuid' in kwargs:
                        return self.authorize_for_user_specific_operation(f, token, *args, **kwargs)

                    # If no specific project or user authorization is required, proceed
                    return f(*args, **kwargs)
                
                except jwt.ExpiredSignatureError:
                    return self.handle_expired_access_token(f, root_required, *args, **kwargs)
                except jwt.InvalidTokenError:
                    return jsonify({"message": "Invalid token."}), 401
            
            return decorated_function
        
        return decorator

    def _authenticate_root(
        self, f: callable, token: str, *args: tuple, **kwargs: dict
    ) -> Response | Any:
        """Method to check whether the current user has root privileges necessary
        to perform sensitive operations.

        Args:
            f (callable): The function to wrap with authorization checks.
            token (str): The JWT access token.
            *args (tuple): Additional arguments for the wrapped function.
            **kwargs (dict): Keyword arguments, including the project ID (`uuid`).

        Returns:
            Response | Any: The response from the wrapped function if authorized, or an
                            error response with status 403 or 404 if unauthorized
        """
        token_payload = self._decode_token(token)
        print('root authenticate method token payload', token_payload)
        if token_payload.get("is_root") == True:
            return f(*args, **kwargs)
        else:
            return jsonify({"message": "Unathorized"}), 403
        
    def _get_token(self) -> str | None:
        """Extracts the token from the Authorization header.

        Returns:
            str | None: The token if present in the "Authorization" header, or None if
            not found.
        """
        auth_header = request.headers.get("Authorization")
        if auth_header and len(auth_header.split(" ")) == 2:
            return auth_header.split(" ")[1]  # Assuming "Bearer <token>"
        return None

    def _decode_token(self, token: str) -> dict:
        """Decodes a JWT token using the secret key.

        Args:
            token (str): The JWT token to decode.

        Returns:
            dict: The decoded token payload.
        """
        return jwt.decode(token, self.secret_key, algorithms=["HS256"])
    
    def authorize_for_user_specific_operation(
            self, f: callable, token: str, *args: tuple, **kwargs: dict
    ) -> Response | Any:
        """Authorizes a user to perform user-specific operations that cannot
        be performed by the root-user, such as updating their password.

        Args:
            f (callable): The function to wrap with authorization checks.
            token (str): The JWT access token.
            *args (tuple): Additional arguments for the wrapped function.
            **kwargs (dict): Keyword arguments, including the project ID (`uuid`).
        
        Returns:
            Response | Any: The response from the wrapped function if authorized, or an
                            error response with status 403 or 404 if unauthorized.
        """
        token_payload = self._decode_token(token)
        user_uuid_in_path = kwargs.get("user_uuid")
        current_session_user_uuid = token_payload.get("user_uuid")
        if current_session_user_uuid:
            # allow root user to bypass user_uuid checks 
            current_session_user_is_root = get_user_root_info(current_session_user_uuid)
            if current_session_user_is_root and f.__name__ == 'get_user_projects':
                return f(*args, **kwargs)
        
            if str(current_session_user_uuid) != str(user_uuid_in_path):
                return jsonify({"message": "Unauthorized"}), 403
            else:
                return f(*args, **kwargs)
        else:
            return jsonify({"message": "Token error"}), 500

    def authorize_user_for_project(
        self, f: callable, token: str, *args: tuple, **kwargs: dict
    ) -> Response | Any:
        """Authorizes a user for access to a specific project by checking if the user ID
        is in the list of authorized users for the project.

        Args:
            f (callable): The function to wrap with authorization checks.
            token (str): The JWT access token.
            *args (tuple): Additional arguments for the wrapped function.
            **kwargs (dict): Keyword arguments, including the project ID (`uuid`).

        Returns:
            Response | Any: The response from the wrapped function if authorized, or an
                            error response with status 403 or 404 if unauthorized.
        """
        token_payload = self._decode_token(token)
        user_uuid = token_payload.get("user_uuid")
        project_uuid = kwargs.get("project_uuid")

        if project_uuid:
            authorized_user_uuids = list(map(lambda user: user['uuid'], fetch_project_users(project_uuid)))
            print('authorized users', authorized_user_uuids)
            if user_uuid in authorized_user_uuids or token_payload.get("is_root") is True:
                return f(*args, **kwargs)
            else:
                return jsonify({"message": "Unauthorized for this project"}), 403

        return f(*args, **kwargs)

    def handle_expired_access_token(
        self, f: callable, root_required: bool, *args: tuple, **kwargs: dict
    ) -> Response:
        """Handles an expired access token by refreshing it
          and re-attempting authorization.

        Args:
            f (callable): The function to wrap with token refresh logic.
            *args (tuple): Additional arguments for the wrapped function.
            **kwargs (dict): Keyword arguments for the wrapped function.

        Returns:
            Response: A new access token response if refreshed, or an error message if
                      the refresh token is invalid or expired.
        """
        # error-handling is built-in in the refresh_token method definition
        parsed_json_data = json.loads(
            get_new_access_token()[0].get_data().decode("utf-8")
        )
        new_access_token = parsed_json_data.get("access_token")
        if new_access_token:
            try:
                print('root required on decorator', root_required)
                response = make_response(
                    self.check_session_and_authorization(root_required)(f)(new_access_token, *args, **kwargs))
                response.headers['New-Access-Token'] = new_access_token
                return response
            # To-do: delete except blocks - errors should be handled by check_session_and_authorization
            except jwt.ExpiredSignatureError:
                return self.handle_expired_access_token(f, *args, **kwargs)
            except jwt.InvalidTokenError:
                return jsonify({"message": "Invalid token."}), 401
        else:
            # return message for invalid or expired refresh token
            return jsonify(parsed_json_data), 403