import logging
import ssl
import httpx
import base64
import uuid
from typing import Optional
from pathlib import Path
from src.config import settings
from src.services.service_decorators import with_retry

logger = logging.getLogger(__name__)


class SaluteSpeechModel:
    """Класс для работы с Salute Speech API"""

    AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    BASE_URL = "https://smartspeech.sber.ru/rest/v1"

    def __init__(self):
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0

        src_root = Path(__file__).resolve().parent.parent
        certificates_dir = src_root / "assets" / "certificates"
        self.cert_path = certificates_dir / "russian_trusted_root_ca.cer"

        self.ssl_context = self._create_ssl_context()

    def _create_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Создание SSL контекста с русскими сертификатами"""
        if not self.cert_path.exists():
            logger.warning(f"Сертификат не найден: {self.cert_path}")
            return None

        try:
            ssl_context = ssl.create_default_context()
            ssl_context.load_verify_locations(cafile=str(self.cert_path))
            logger.info("✓ Salute: SSL контекст создан с сертификатом")
            return ssl_context
        except Exception as e:
            logger.error(f"✗ Salute: Ошибка создания SSL контекста: {e}")
            return None

    def _get_httpx_client_kwargs(self) -> dict:
        """Получение параметров для httpx.AsyncClient"""
        if self.ssl_context:
            return {"verify": self.ssl_context}
        else:
            logger.warning("Salute: Использование verify=False (сертификат недоступен)")
            return {"verify": False}

    @with_retry
    async def _get_auth_token(self) -> str:
        """Получение токена авторизации с retry"""
        auth_string = f"{settings.SALUTE_CLIENT_ID}:{settings.SALUTE_CLIENT_SECRET}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_encoded}",
            "RqUID": str(uuid.uuid4()),
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {"scope": settings.SALUTE_SCOPE}

        try:
            async with httpx.AsyncClient(**self._get_httpx_client_kwargs()) as client:
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
                logger.error(error_detail)
            except ValueError:
                error_detail = e.response.text
                logger.error(error_detail)
            raise Exception(
                f"Ошибка авторизации Salute: HTTP {e.response.status_code}: {error_detail}"
            )
        except Exception as e:
            logger.error(e)
            raise Exception(f"Ошибка получения токена Salute: {str(e)}")

    async def _ensure_token(self):
        """Проверка и обновление токена при необходимости"""
        import time

        if not self.access_token or time.time() >= (self.token_expires_at - 60):
            self.access_token = await self._get_auth_token()
            self.token_expires_at = time.time() + (29 * 60)

    @with_retry
    async def transcribe_audio(
        self, audio_data: bytes, audio_format: str = "opus"
    ) -> str:
        """
        Транскрибация аудио

        Args:
            audio_data: Байты аудиофайла
            audio_format: Формат аудио (opus, pcm16, mp3, flac, wav)

        Returns:
            Распознанный текст
        """
        await self._ensure_token()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }

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

        try:
            async with httpx.AsyncClient(**self._get_httpx_client_kwargs()) as client:
                response = await client.post(
                    f"{self.BASE_URL}/speech:recognize",
                    headers=headers,
                    params=params,
                    content=audio_data,
                    timeout=60.0,
                )

                if response.status_code == 401:
                    self.access_token = None
                    await self._ensure_token()
                    headers["Authorization"] = f"Bearer {self.access_token}"

                    response = await client.post(
                        f"{self.BASE_URL}/speech:recognize",
                        headers=headers,
                        params=params,
                        content=audio_data,
                        timeout=60.0,
                    )

                response.raise_for_status()
                result = response.json()

                res_arr = result.get("result", [])
                text_res = " ".join(res_arr)
                return text_res

        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = e.response.json()
            except ValueError:
                error_detail = e.response.text
            raise Exception(
                f"Ошибка транскрибации: HTTP {e.response.status_code}: {error_detail}"
            )

    async def transcribe_from_file(
        self, file_path: str, audio_format: Optional[str] = None
    ) -> str:
        """
        Транскрибация аудио из файла

        Args:
            file_path: Путь к аудиофайлу
            audio_format: Формат аудио (определяется автоматически по расширению)

        Returns:
            Распознанный текст
        """
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

        with open(file_path, "rb") as f:
            audio_data = f.read()

        return await self.transcribe_audio(audio_data, audio_format)
