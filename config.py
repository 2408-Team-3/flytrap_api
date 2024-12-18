"""Configuration module for loading environment variables."""

import os
import json

class TestingConfig:
    """Testing configuration."""
    DB_HOST = "localhost"
    DB_PORT = 5433
    DB_NAME = "test_db"
    DB_USER = "postgres"
    DB_PASSWORD = "postgres"
    JWT_SECRET_KEY = '23ljdskj3jh23b432k'

class StandardConfig:
    """Development and Production configuration."""
    DB_HOST = os.getenv("PGHOST")
    DB_NAME = os.getenv("PGDATABASE")
    DB_USER = os.getenv("PGUSER")
    DB_PORT = os.getenv("PGPORT")
    HTTPONLY = os.getenv("HTTPONLY") == "True"
    SECURE = os.getenv("SECURE") == "True"
    SAMESITE = os.getenv("SAMESITE")


def load_config(app):
    """
    Dynamically load configuration into the Flask app.
    This includes environment variables and secrets from AWS Secrets Manager.
    """
    app.config["ENVIRONMENT"] = os.getenv("FLASK_ENV", "development")

    if app.config["ENVIRONMENT"] == 'TESTING':
        app.config.from_object(TestingConfig)

    else:
        if app.config["ENVIRONMENT"] == "development":
            from dotenv import load_dotenv

            load_dotenv()

            app.config["DB_PASSWORD"] = os.getenv("PGPASSWORD")
            app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
        else:
            """Set production configuration"""
            from app.utils import get_secret

            try:
                # Load secrets from AWS Secrets Manager
                jwt_secret = get_secret("jwt_secret_key", app.config["AWS_REGION"])
                app.config["JWT_SECRET_KEY"] = json.loads(jwt_secret)["jwt_secret_key"]

                db_credentials = get_secret(
                    "flytrap_db_credentials", app.config["AWS_REGION"]
                )
                app.config["DB_PASSWORD"] = json.loads(db_credentials)["password"]
            except Exception as e:
                app.logger.error(f"Failed to load secrets: {e}")
                app.config["DB_PASSWORD"] = None
                app.config["JWT_SECRET_KEY"] = None
                raise e
        
        # Load configuration settings that are shared between development and production
        app.config.from_object(StandardConfig)