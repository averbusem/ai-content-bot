import httpx
import base64
import uuid
from typing import Optional, List, Dict
from src.config import settings


class GigaChatModel:
    """Класс для работы с GigaChat API"""

    AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    BASE_URL = "https://gigachat.devices.sberbank.ru/api/v1"

    def __init__(self):
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0
        self.conversation_history: List[Dict[str, str]] = []

    async def _get_auth_token(self) -> str:
        """Получение токена авторизации"""
        auth_string = f"{settings.GIGACHAT_CLIENT_ID}:{settings.GIGACHAT_CLIENT_SECRET}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_encoded}",
            "RqUID": str(uuid.uuid4()),
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {"scope": settings.GIGACHAT_SCOPE}

        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(
                    self.AUTH_URL, headers=headers, data=data, timeout=30.0
                )
                response.raise_for_status()
                token_data = response.json()
                return token_data["access_token"]
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = e.response.json()
            except ValueError:
                error_detail = e.response.text
            raise Exception(
                f"Ошибка авторизации GigaChat: HTTP {e.response.status_code}: {error_detail}"
            )
        except Exception as e:
            raise Exception(f"Ошибка получения токена GigaChat: {str(e)}")

    async def _ensure_token(self):
        """Проверка и обновление токена при необходимости"""
        import time

        if not self.access_token or time.time() >= (self.token_expires_at - 60):
            self.access_token = await self._get_auth_token()
            self.token_expires_at = time.time() + (30 * 60)

    async def analyze_image(
        self, image_data: bytes, prompt: str = "Подробно опиши это изображение"
    ) -> str:
        await self._ensure_token()

        headers = {"Authorization": f"Bearer {self.access_token}"}

        async with httpx.AsyncClient(verify=False) as client:
            try:
                files = {"file": ("image.jpg", image_data, "image/jpeg")}

                data = {"purpose": "general"}

                upload_response = await client.post(
                    f"{self.BASE_URL}/files",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=60.0,
                )

                if upload_response.status_code == 401:
                    self.access_token = None
                    await self._ensure_token()
                    headers["Authorization"] = f"Bearer {self.access_token}"

                    upload_response = await client.post(
                        f"{self.BASE_URL}/files",
                        headers=headers,
                        files=files,
                        data=data,
                        timeout=60.0,
                    )

                upload_response.raise_for_status()
                file_info = upload_response.json()
                file_id = file_info.get("id")

                if not file_id:
                    raise Exception("Не удалось загрузить изображение")

                headers["Content-Type"] = "application/json"

                payload = {
                    "model": "GigaChat-Pro",
                    "messages": [
                        {"role": "user", "content": prompt, "attachments": [file_id]}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000,
                }

                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60.0,
                )

                if response.status_code == 401:
                    self.access_token = None
                    await self._ensure_token()
                    headers["Authorization"] = f"Bearer {self.access_token}"

                    response = await client.post(
                        f"{self.BASE_URL}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=60.0,
                    )

                response.raise_for_status()
                result = response.json()

                return result["choices"][0]["message"]["content"]

            except httpx.HTTPStatusError as e:
                error_detail = ""
                try:
                    error_detail = e.response.json()
                except ValueError:
                    error_detail = e.response.text
                raise Exception(
                    f"Ошибка анализа изображения: HTTP {e.response.status_code}: {error_detail}"
                )

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        use_history: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
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
            messages.append({"role": "system", "content": system_prompt})

        if use_history and self.conversation_history:
            messages.extend(self.conversation_history)

        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": settings.GIGACHAT_MODEL,
            "messages": messages,
            "temperature": temperature or settings.AI_TEMPERATURE,
            "max_tokens": max_tokens or settings.AI_MAX_TOKENS,
            "repetition_penalty": 1.1,
        }

        async with httpx.AsyncClient(verify=False) as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60.0,
                )

                if response.status_code == 401:
                    self.access_token = None
                    await self._ensure_token()
                    headers["Authorization"] = f"Bearer {self.access_token}"

                    response = await client.post(
                        f"{self.BASE_URL}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=60.0,
                    )

                response.raise_for_status()
                result = response.json()

                generated_text = result["choices"][0]["message"]["content"]

                if use_history:
                    self.conversation_history.append(
                        {"role": "user", "content": prompt}
                    )
                    self.conversation_history.append(
                        {"role": "assistant", "content": generated_text}
                    )

                    if len(self.conversation_history) > 20:
                        self.conversation_history = self.conversation_history[-20:]

                return generated_text

            except httpx.HTTPStatusError as e:
                error_detail = ""
                try:
                    error_detail = e.response.json()
                except ValueError:
                    error_detail = e.response.text
                raise Exception(f"HTTP {e.response.status_code}: {error_detail}")

    async def generate_image(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
    ) -> bytes:
        """
        Генерация изображения (БЕЗ исходного изображения)

        Args:
            prompt: Промпт для генерации
            system_prompt: Системный промпт
            width: Ширина изображения
            height: Высота изображения

        Returns:
            Байты изображения
        """
        await self._ensure_token()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": f"Создай изображение: {prompt}"})

        payload = {
            "model": "GigaChat",
            "messages": messages,
            "function_call": "auto",
            "width": width,
            "height": height,
        }

        async with httpx.AsyncClient(verify=False) as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=120.0,
                )

                if response.status_code == 401:
                    self.access_token = None
                    await self._ensure_token()
                    headers["Authorization"] = f"Bearer {self.access_token}"

                    response = await client.post(
                        f"{self.BASE_URL}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=120.0,
                    )

                response.raise_for_status()
                result = response.json()

                content = result["choices"][0]["message"]["content"]

                import re

                file_id_match = re.search(r'<img.*?src="([^"]+)"', content)
                if not file_id_match:
                    raise ValueError("Не удалось получить file_id изображения")

                file_id = file_id_match.group(1)

                image_response = await client.get(
                    f"{self.BASE_URL}/files/{file_id}/content",
                    headers=headers,
                    timeout=60.0,
                )
                image_response.raise_for_status()

                return image_response.content

            except httpx.HTTPStatusError as e:
                error_detail = ""
                try:
                    error_detail = e.response.json()
                except ValueError:
                    error_detail = e.response.text
                raise Exception(f"HTTP {e.response.status_code}: {error_detail}")

    def clear_history(self):
        self.conversation_history = []

    def get_history(self) -> List[Dict[str, str]]:
        return self.conversation_history.copy()
