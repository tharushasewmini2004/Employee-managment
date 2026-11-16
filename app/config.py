# app/config.py
import os

from dotenv import load_dotenv

load_dotenv()  # reads the .env file in the project folder (does nothing if there is none)


def _get_int(name, default):
    """Read a whole-number setting, or use the default if it is not set."""
    value = os.getenv(name)
    return int(value) if value else default


class Settings:
    """All configuration in one place. Values come from environment variables."""

    APP_NAME = os.getenv("APP_NAME", "Employee Management API")
    APP_ENV = os.getenv("APP_ENV", "development")
    DATABASE_URL = os.getenv("DATABASE_URL")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    DEFAULT_PAGE_SIZE = _get_int("DEFAULT_PAGE_SIZE", 20)
    MAX_PAGE_SIZE = _get_int("MAX_PAGE_SIZE", 100)


settings = Settings()