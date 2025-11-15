from dataclasses import dataclass
from os import getenv


@dataclass
class BotConfig:
    """Конфигурация Telegram бота"""
    token: str


@dataclass
class GigaChatSettings:
    """Настройки GigaChat"""
    client_id: str
    client_secret: str
    model: str = "GigaChat"
    temperature: float = 0.7
    max_tokens: int = 2048


@dataclass
class SaluteSpeechSettings:
    """Настройки Salute Speech"""
    client_id: str
    client_secret: str
    scope: str = "SALUTE_SPEECH_PERS"


@dataclass
class Config:
    """Общая конфигурация"""
    bot: BotConfig
    gigachat: GigaChatSettings
    salute_speech: SaluteSpeechSettings


def load_config() -> Config:
    """
    Загрузка конфигурации из переменных окружения

    Returns:
        Объект конфигурации
    """
    return Config(
        bot=BotConfig(
            token=getenv("BOT_TOKEN", "")
        ),
        gigachat=GigaChatSettings(
            client_id=getenv("GIGACHAT_CLIENT_ID", ""),
            client_secret=getenv("GIGACHAT_CLIENT_SECRET", ""),
            model=getenv("GIGACHAT_MODEL", "GigaChat"),
            temperature=float(getenv("AI_TEMPERATURE", "0.7")),
            max_tokens=int(getenv("AI_MAX_TOKENS", "2048"))
        ),
        salute_speech=SaluteSpeechSettings(
            client_id=getenv("SALUTE_CLIENT_ID", ""),
            client_secret=getenv("SALUTE_CLIENT_SECRET", "")
        )
    )