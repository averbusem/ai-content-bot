from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


env_path = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(env_path), case_sensitive=True, extra="ignore"
    )

    # Telegram Bot
    BOT_TOKEN: str = ""

    REDIS_HOST: str = ""
    REDIS_PORT: str = ""
    REDIS_PASSWORD: str = ""
    REDIS_DB: str = "0"

    @property
    def REDIS_URL(self) -> str:
        url = (
            f"redis://:{self.REDIS_PASSWORD}@"
            f"{self.REDIS_HOST}:{self.REDIS_PORT}"
            f"/{self.REDIS_DB}"
        )
        return url

    # GigaChat
    GIGACHAT_CLIENT_ID: str = ""
    GIGACHAT_CLIENT_SECRET: str = ""
    GIGACHAT_SCOPE: str = "GIGACHAT_API_PERS"
    GIGACHAT_MODEL: str = "GigaChat"
    AI_TEMPERATURE: float = 0.7
    AI_MAX_TOKENS: int = 2048

    # Salute Speech
    SALUTE_CLIENT_ID: str = ""
    SALUTE_CLIENT_SECRET: str = ""
    SALUTE_SCOPE: str = "SALUTE_SPEECH_PERS"

    # User operations limit
    USER_OPERATIONS_LIMIT: int = int(1)
    USER_OPERATIONS_WINDOW: int = int(360)

    # Rate Limiter
    MAX_RETRIES: int = int(3)
    RETRY_MIN_WAIT: int = int(1)
    RETRY_MAX_WAIT: int = int(10)


settings = Settings()
