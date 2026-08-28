from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./messenger.db"

    security_max_failures: int = 5
    security_failure_window_seconds: float = 300.0
    security_ban_seconds: float = 900.0
    security_ban_escalate_factor: float = 2.0
    security_ban_max_seconds: float = 86400.0
    security_max_connect_attempts: int = 20
    security_connect_window_seconds: float = 60.0
    security_max_concurrent_per_ip: int = 3
    security_auth_timeout_seconds: float = 8.0
    security_max_messages_per_window: int = 60
    security_message_window_seconds: float = 10.0
    # comma-separated permanent ban list, e.g. "1.2.3.4,5.6.7.8"
    security_permanent_bans: str = ""


settings = Settings()
