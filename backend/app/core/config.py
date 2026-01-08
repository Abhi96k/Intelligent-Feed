"""Application configuration."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    VERSION: str = "1.0.0"

    # LLM Provider (anthropic or openai)
    LLM_PROVIDER: str = "openai"  # or "anthropic"
    
    # Anthropic API (optional if using OpenAI)
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    ANTHROPIC_MAX_TOKENS: int = 4096
    ANTHROPIC_TEMPERATURE: float = 0.0
    
    # OpenAI API (optional if using Anthropic)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MAX_TOKENS: int = 4096
    OPENAI_TEMPERATURE: float = 0.0

    # Database
    DATABASE_URL: str = "sqlite:///./tellius_feed.db"

    # Python Sandbox
    SANDBOX_TIMEOUT: int = 30  # seconds
    SANDBOX_MEMORY_LIMIT_MB: int = 512

    # Detection Thresholds
    DEFAULT_ABSOLUTE_THRESHOLD: float = 5.0  # percentage
    DEFAULT_ARIMA_SENSITIVITY: float = 2.0  # sigma multiplier (lower = more sensitive)

    # Query Limits
    MAX_QUERY_ROWS: int = 1000000
    QUERY_TIMEOUT: int = 30  # seconds

    # Deep Insight Configuration
    MAX_DRIVERS_TO_ANALYZE: int = 20
    TOP_DRIVERS_TO_RETURN: int = 10
    MIN_CONTRIBUTION_THRESHOLD: float = 0.01  # 1%

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
