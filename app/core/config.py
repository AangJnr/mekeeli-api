import os
from dataclasses import dataclass


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "Mekeeli API")
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./sql.db")
    worker_poll_interval: int = int(os.getenv("WORKER_POLL_INTERVAL", "10"))
    offline_mode_default: bool = os.getenv("OFFLINE_MODE_DEFAULT", "true").lower() == "true"


settings = Settings()
