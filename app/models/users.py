"""Users models module.

This module provides functions for managing users in the database, including fetching
all users, adding new users, deleting users, updating user passwords, and retrieving
user information by email or user ID. Each function is decorated to ensure the
appropriate database connection context for reading or writing.
"""

from typing import List, Dict, Optional, Union
from app.utils import (
    db_read_connection,
    db_write_connection,
    generate_uuid,
    calculate_total_user_project_pages,
)


@db_read_connection
def fetch_all_users(**kwargs) -> Optional[List[Dict[str, str]]]:
    """Retrieves a list of all users in the database."""
    cursor = kwargs["cursor"]

    query = "SELECT uuid, first_name, last_name, email, is_root, created_at FROM users;"
    cursor.execute(query)
    rows = cursor.fetchall()

    users = [
        {
            "uuid": user[0],
            "first_name": user[1],
            "last_name": user[2],
            "email": user[3],
            "is_root": user[4],
            "created_at": user[5],
        }
        for user in rows
    ]

    return users


@db_write_connection
def add_user(
    first_name: str, last_name: str, email: str, password_hash: str, **kwargs
) -> int:
    """Adds a new user to the database with the specified information."""
    connection = kwargs["connection"]
    cursor = kwargs["cursor"]

    user_uuid = generate_uuid()

    query = """
    INSERT INTO users
    (uuid, first_name, last_name, email, password_hash)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING id;
    """
    cursor.execute(query, (user_uuid, first_name, last_name, email, password_hash))
    connection.commit()

    return user_uuid


@db_write_connection
def delete_user_by_id(user_uuid: str, **kwargs) -> bool:
    """Deletes a user by their unique user ID."""
    connection = kwargs["connection"]
    cursor = kwargs["cursor"]
    query = "DELETE FROM users WHERE uuid = %s"
    cursor.execute(query, (user_uuid,))
    rows_deleted = cursor.rowcount
    connection.commit()

    return rows_deleted > 0


@db_write_connection
def update_password(user_uuid: str, password_hash: str, **kwargs) -> bool:
    """Updates the password hash for a specific user."""
    connection = kwargs["connection"]
    cursor = kwargs["cursor"]

    query = """
    UPDATE users
    SET password_hash = %s
    WHERE uuid = %s
    """

    cursor.execute(query, (password_hash, user_uuid))
    rows_updated = cursor.rowcount
    connection.commit()

    return rows_updated > 0


@db_read_connection
def fetch_user_by_email(
    email: str, **kwargs
) -> Optional[Dict[str, Union[int, str, bool]]]:
    """Retrieves user data by email, including password hash and root status."""
    cursor = kwargs["cursor"]

    query = """
    SELECT
        u.uuid, u.first_name, u.last_name, u.password_hash, u.is_root
    FROM users u
    WHERE u.email = %s;
    """
    cursor.execute(query, (email,))
    user = cursor.fetchone()
    if user:
        return {
            "uuid": user[0],
            "first_name": user[1],
            "last_name": user[2],
            "password_hash": user[3],
            "is_root": user[4],
        }

    return None


@db_read_connection
def user_is_root(user_uuid, **kwargs):
    """Retrieves the root access status for a specific user by their unique ID.

    Args:
        user_id (str): The unique uuid of the user.

    Returns:
        bool: True if the user has root access, False otherwise.
    """
    cursor = kwargs["cursor"]

    query = """
    SELECT is_root
    FROM users
    WHERE uuid = %s
    """
    cursor.execute(query, (user_uuid,))
    is_root = cursor.fetchone()[0]

    return is_root


@db_read_connection
def fetch_projects_for_user(user_uuid, page: int, limit: int, **kwargs) -> dict:
    """Fetches all projects assigned to a specific user by user ID."""
    cursor = kwargs["cursor"]
    offset = (page - 1) * limit if limit else 0

    query = """
    SELECT
        p.uuid,
        p.name,
        p.platform,
        COUNT(DISTINCT e.id) AS error_count,
        COUNT(DISTINCT r.id) AS rejection_count
    FROM
        projects p
    JOIN
        projects_users pu ON p.id = pu.project_id
    JOIN
        users u ON pu.user_id = u.id
    LEFT JOIN
        error_logs e ON e.project_id = p.id
    LEFT JOIN
        rejection_logs r ON r.project_id = p.id
    WHERE
        u.uuid = %s
    GROUP BY
        p.uuid, p.name, p.platform
    ORDER BY p.name
    LIMIT %s OFFSET %s;
    """

    cursor.execute(query, (user_uuid, limit, offset))
    rows = cursor.fetchall()

    projects = [
        {
            "uuid": project[0],
            "name": project[1],
            "platform": project[2],
            "issue_count": project[3] + project[4],
        }
        for project in rows
    ]

    total_pages = calculate_total_user_project_pages(cursor, user_uuid, limit)

    return {
        "projects": projects,
        "total_pages": total_pages,
        "current_page": int(page),
    }


@db_read_connection
def get_user_info(user_uuid: str, **kwargs) -> dict:
    """Fetches a user's uuid, first and last name, email, and root status."""
    cursor = kwargs["cursor"]

    query = "SELECT first_name, last_name, email, is_root FROM users WHERE uuid = %s;"
    cursor.execute(query, (user_uuid,))
    user = cursor.fetchone()

    return {
        "user_uuid": user_uuid,
        "first_name": user[0],
        "last_name": user[1],
        "email": user[2],
        "is_root": user[3]
    }
