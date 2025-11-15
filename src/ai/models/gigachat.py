import httpx
import base64
import uuid
from typing import Optional, List, Dict
from dataclasses import dataclass


@dataclass
class GigaChatConfig:
    """Конфигурация для GigaChat"""
    client_id: str
    client_secret: str
    scope: str = "GIGACHAT_API_PERS"
    model: str = "GigaChat"
    temperature: float = 0.7
    max_tokens: int = 2048


class GigaChatModel:
    """Класс для работы с GigaChat API"""

    AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    BASE_URL = "https://gigachat.devices.sberbank.ru/api/v1"

    def __init__(self, config: GigaChatConfig):
        self.config = config
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0
        self.conversation_history: List[Dict[str, str]] = []

    async def _get_auth_token(self) -> str:
        """Получение токена авторизации"""
        auth_string = f"{self.config.client_id}:{self.config.client_secret}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_encoded}",
            "RqUID": str(uuid.uuid4()),
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "scope": self.config.scope
        }

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                self.AUTH_URL,
                headers=headers,
                data=data,
                timeout=30.0
            )
            response.raise_for_status()
            token_data = response.json()
            return token_data["access_token"]

    async def _ensure_token(self):
        """Проверка и обновление токена при необходимости"""
        import time
        if not self.access_token or time.time() >= self.token_expires_at:
            self.access_token = await self._get_auth_token()
            self.token_expires_at = time.time() + (29 * 60)

    async def generate_text(
            self,
            prompt: str,
            system_prompt: Optional[str] = None,
            use_history: bool = False,
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None
    ) -> str:
        """
        Генерация текста

        Args:
            prompt: Запрос пользователя
            system_prompt: Системный промпт для настройки поведения
            use_history: Использовать ли историю диалога
            temperature: Температура генерации (креативность)
            max_tokens: Максимальное количество токенов

        Returns:
            Сгенерированный текст
        """
        await self._ensure_token()

        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        if use_history and self.conversation_history:
            messages.extend(self.conversation_history)

        messages.append({
            "role": "user",
            "content": prompt
        })

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "repetition_penalty": 1.1
        }

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()

            generated_text = result["choices"][0]["message"]["content"]

            if use_history:
                self.conversation_history.append({
                    "role": "user",
                    "content": prompt
                })
                self.conversation_history.append({
                    "role": "assistant",
                    "content": generated_text
                })

                # Ограничиваем историю (например, последние 10 сообщений)
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]

            return generated_text

    async def generate_image(
            self,
            prompt: str,
            width: int = 1024,
            height: int = 1024
    ) -> bytes:
        await self._ensure_token()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "GigaChat",
            "messages": [
                {
                    "role": "user",
                    "content": f"Создай изображение: {prompt}"
                }
            ],
            "function_call": "auto",
            "width": width,
            "height": height
        }

        async with httpx.AsyncClient(verify=False) as client:
            # Запрос на генерацию
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120.0
            )
            response.raise_for_status()
            result = response.json()

            # Получаем file_id изображения
            content = result["choices"][0]["message"]["content"]

            # Ищем file_id в ответе
            import re
            file_id_match = re.search(r'<img.*?src="([^"]+)"', content)
            if not file_id_match:
                raise ValueError("Не удалось получить file_id изображения")

            file_id = file_id_match.group(1)

            # Скачиваем изображение
            image_response = await client.get(
                f"{self.BASE_URL}/files/{file_id}/content",
                headers=headers,
                timeout=60.0
            )
            image_response.raise_for_status()

            return image_response.content

    def clear_history(self):
        """Очистка истории диалога"""
        self.conversation_history = []

    def get_history(self) -> List[Dict[str, str]]:
        """Получение истории диалога"""
        return self.conversation_history.copy()