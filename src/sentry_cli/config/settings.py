"""Settings configuration with environment variable loading from ~/.claude/.env and ./.env"""
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env files.

    Loading priority (highest to lowest):
    1. Environment variables from shell
    2. ~/.claude/.env (user-level config)
    3. ./.env (project-level config)
    4. Default values
    """

    model_config = SettingsConfigDict(
        env_file=[
            Path.home() / ".claude" / ".env",  # User-level for all AI assistants
            ".env",                            # Project-level
        ],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Sentry configuration
    sentry_access_token: str = Field(
        ...,
        description="Sentry API access token (required)",
    )
    sentry_host: str = Field(
        default="sentry.io",
        description="Sentry host for self-hosted instances",
    )
    sentry_default_org: Optional[str] = Field(
        default=None,
        description="Default organization slug",
    )
    sentry_default_project: Optional[str] = Field(
        default=None,
        description="Default project slug",
    )

    # OpenAI configuration (optional - enables AI-powered search)
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for search_events and search_issues tools",
    )

    # Output preferences (optimized for AI assistants)
    output_format: str = Field(
        default="json",
        description="Default output format: json, table, or compact",
    )
    output_color: bool = Field(
        default=False,
        description="Enable colored output (disabled by default for AI assistants)",
    )


def get_settings() -> Settings:
    """
    Get application settings.

    Returns:
        Settings instance with configuration loaded from env vars and .env files

    Raises:
        ValidationError: If required settings (like sentry_access_token) are missing
    """
    return Settings()
