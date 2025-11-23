import httpx
import base64
import uuid
from typing import Optional
from pathlib import Path
from src.config import settings


class SaluteSpeechModel:
    """Класс для работы с Salute Speech API"""

    AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    BASE_URL = "https://smartspeech.sber.ru/rest/v1"

    def __init__(self):
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0

    async def _get_auth_token(self) -> str:
        auth_string = f"{settings.SALUTE_CLIENT_ID}:{settings.SALUTE_CLIENT_SECRET}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_encoded}",
            "RqUID": str(uuid.uuid4()),
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {"scope": settings.SALUTE_SCOPE}

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                self.AUTH_URL, headers=headers, data=data, timeout=30.0
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

    async def transcribe_audio(
        self, audio_data: bytes, audio_format: str = "opus"
    ) -> str:
        await self._ensure_token()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }

        # Определяем MIME тип
        mime_types = {
            "opus": "audio/ogg;codecs=opus",
            "pcm16": "audio/x-pcm;bit=16;rate=8000",
            "mp3": "audio/mpeg",
            "flac": "audio/flac",
            "wav": "audio/wav",
        }

        content_type = mime_types.get(audio_format, "audio/ogg;codecs=opus")

        headers["Content-Type"] = content_type

        params = {"format": audio_format if audio_format != "opus" else "ogg_opus"}

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{self.BASE_URL}/speech:recognize",
                headers=headers,
                params=params,
                content=audio_data,
                timeout=60.0,
            )

            response.raise_for_status()
            result = response.json()

            res_arr = result.get("result", "")
            text_res = " ".join(res_arr)
            return text_res

    async def transcribe_from_file(
        self, file_path: str, audio_format: Optional[str] = None
    ) -> str:
        path = Path(file_path)

        if not audio_format:
            ext = path.suffix.lower().lstrip(".")
            format_map = {
                "ogg": "opus",
                "opus": "opus",
                "wav": "pcm16",
                "mp3": "mp3",
                "flac": "flac",
            }
            audio_format = format_map.get(ext, "opus")

        # Читаем файл
        with open(file_path, "rb") as f:
            audio_data = f.read()

        return await self.transcribe_audio(audio_data, audio_format)
