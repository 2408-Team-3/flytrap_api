"""Utilities package initializer."""

from .db_helpers import (
    calculate_total_project_pages,
    fetch_errors_by_project,
    fetch_rejections_by_project,
    calculate_total_error_pages,
    calculate_total_user_project_pages,
)
from .uuid_generator import generate_uuid
from .validation import is_valid_email
from .aws_helpers import (
    create_aws_client,
    get_secret,
    associate_api_key_with_usage_plan,
    create_sns_topic,
    create_sns_subscription,
    remove_sns_subscription,
    send_sns_notification,
    delete_api_key_from_aws,
    delete_sns_topic_from_aws,
)

__all__ = [
    "calculate_total_project_pages",
    "fetch_errors_by_project",
    "fetch_rejections_by_project",
    "calculate_total_error_pages",
    "generate_uuid",
    "is_valid_email",
    "calculate_total_user_project_pages",
    "create_aws_client",
    "get_secret",
    "associate_api_key_with_usage_plan",
    "create_sns_topic",
    "create_sns_subscription",
    "remove_sns_subscription",
    "send_sns_notification",
    "delete_api_key_from_aws",
    "delete_sns_topic_from_aws",
]
