from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "JobFit AI - LinkedIn Job Matcher & Telegram Notifier"
    VERSION: str = "1.0.0"

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: Optional[str] = ""
    TELEGRAM_CHAT_ID: Optional[str] = ""

    # Defaults (Unlimited jobs by default)
    DEFAULT_JOB_KEYWORDS: str = "Python FastAPI Developer"
    DEFAULT_JOB_LOCATION: str = "Remote"
    DEFAULT_MIN_MATCH_PERCENTAGE: int = 55
    DEFAULT_MAX_JOBS: int = 0  # 0 = Unlimited (All Available Jobs)

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000


settings = Settings()
